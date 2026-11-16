"""Value noise and fractal Brownian motion in 2D, plus scalar helpers.

Ported from abyssal-garden's ``ihash`` / ``vnoise`` / ``fbm``
(Noniv/abyssal-garden, MIT): the same lattice hash, the same smoothstep
interpolation, and the same octave constants (scale 2.03, amplitude decay
0.5), so fields generated here share the source project's texture.
"""

from __future__ import annotations

from math import floor

_MASK = 0xFFFFFFFF


def _ihash2(x: int, y: int) -> float:
    """Deterministic hash of an integer lattice point, in [0, 1)."""
    h = (x * 374761393 + y * 668265263) & _MASK
    h = ((h ^ (h >> 13)) * 1274126177) & _MASK
    return ((h ^ (h >> 16)) & _MASK) / 4294967296.0


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else min(x, hi)


def mix(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ss(a: float, b: float, x: float) -> float:
    """Smoothstep from 0 at ``a`` to 1 at ``b``."""
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def vnoise2(x: float, y: float) -> float:
    """Smoothed value noise in [0, 1)."""
    ix, iy = floor(x), floor(y)
    fx, fy = x - ix, y - iy
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    a = mix(_ihash2(ix, iy), _ihash2(ix + 1, iy), ux)
    b = mix(_ihash2(ix, iy + 1), _ihash2(ix + 1, iy + 1), ux)
    return mix(a, b, uy)


def fbm2(x: float, y: float, octaves: int = 4) -> float:
    """Fractal sum of value-noise octaves, normalized to [0, 1)."""
    amp = 0.5
    total = 0.0
    for _ in range(octaves):
        total += amp * vnoise2(x, y)
        x = x * 2.03 + 17.1
        y = y * 2.03 + 31.7
        amp *= 0.5
    return total / (1.0 - amp * 2.0)
