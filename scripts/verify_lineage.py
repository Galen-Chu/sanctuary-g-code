"""Lineage verification: the Python port next to the original JS implementation.

Run both and compare::

    node scripts/verify_lineage.mjs > js.txt
    python scripts/verify_lineage.py > py.txt   # (PYTHONPATH=src)
    diff js.txt py.txt

Lines must be identical. Floats are k/2**32 (RNG) or noise in [0, 1); both
sides compute them as exact IEEE doubles, so equality is exact, not fuzzy.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sanctuary.noise import vnoise2
from sanctuary.rng import Stream, Streams

_BASE = 20261110  # abyssal-garden's own default seed


def _fmt(v: float) -> str:
    """Match JS String(number): shortest round-trip, integral floats print bare."""
    s = repr(v)
    return s[:-2] if s.endswith(".0") else s


# (a) 20 draws from the default seed
stream = Stream(_BASE)
for _ in range(20):
    print(f"a {_fmt(stream.f01())}")

# (b) stream 3 of the same base seed (the rseed(3) pattern)
stream3 = Streams(_BASE).stream(3)
for _ in range(10):
    print(f"b {_fmt(stream3.f01())}")

# (c) the 2D port vs the z=0 slice of the original 3D noise
for x, y in ((0.3, 7.9), (-12.4, 3.1), (25.0, -8.2), (4.7, 4.7), (0.0, 0.0)):
    print(f"c {_fmt(vnoise2(x, y))}")
