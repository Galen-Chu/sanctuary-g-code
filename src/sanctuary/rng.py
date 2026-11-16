"""Deterministic per-system RNG streams (mulberry32).

Ported from abyssal-garden's ``rnd`` / ``rseed`` pattern (Noniv/abyssal-garden,
MIT): one PRNG stream per generator system, so changing one system's draws
never perturbs any other system's output.

Why not Python's ``random``: the standard library only guarantees a stable
``random()`` sequence across versions; a self-contained PRNG keeps generated
worlds byte-identical across Python versions and machines — and, because this
is the same algorithm abyssal-garden runs in JavaScript, the same seeds will
drive the future WebGPU preview with identical numbers.
"""

from __future__ import annotations

_MASK = 0xFFFFFFFF
_OFFSET = 7919  # per-system offset, mirroring abyssal-garden's rseed()


class Stream:
    """A single mulberry32 stream. ``f01`` is uniform in [0, 1)."""

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK

    def next_u32(self) -> int:
        state = (self._state + 0x6D2B79F5) & _MASK
        self._state = state
        t = ((state ^ (state >> 15)) * (state | 1)) & _MASK
        t = (t + (((t ^ (t >> 7)) * (t | 61)) & _MASK) & _MASK) ^ t
        return (t ^ (t >> 14)) & _MASK

    def f01(self) -> float:
        """Next uniform float in [0, 1)."""
        return self.next_u32() / 4294967296.0

    def range(self, lo: float, hi: float) -> float:
        """Next uniform float in [lo, hi)."""
        return lo + (hi - lo) * self.f01()


class Streams:
    """Named per-system stream factory from one base seed.

    Stream ``i`` is seeded ``base + i * _OFFSET``. System ids are a stability
    contract (see docs/DESIGN.md): existing ids never change meaning; a new
    generator system takes the next free id, and previously generated worlds
    stay byte-identical.
    """

    def __init__(self, base_seed: int) -> None:
        self._base = base_seed & _MASK

    def stream(self, system_id: int) -> Stream:
        return Stream((self._base + system_id * _OFFSET) & _MASK)
