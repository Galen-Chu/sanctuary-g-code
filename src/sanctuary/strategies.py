"""Patrol strategy library: how predators schedule visits and choose targets.

Four strategies, each behaviourally distinguishable in statistics (hour
distribution, target choice) — they are the problem statements for
Unbodysoma's learning experiments (BACKLOG section 1):

- ``fixed``      Phase 1 behaviour: daytime slots {11, 14, 17, 20} cyclically,
                 distinct patches. Learnable and predictable.
- ``sweep``      Unpredictable: hours uniform over the whole 24 h day,
                 random patch order.
- ``circadian``  A learnable rhythm: strict 6 h period, one phase draw per
                 world, tiny jitter.
- ``regional``   Regional focus: every visit lands on one anchor patch,
                 hours in the fixed slots — predation empties a region and
                 forces migration.

Draw discipline: a strategy draws only from the patrol stream handed to it,
in its own order. ``fixed`` preserves the original draw order bit-for-bit;
the others are new vocabulary and define their own.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from .rng import Stream
from .world import FoodPatch, Hazard

if TYPE_CHECKING:
    from .systems import Generation

_SLOTS = (11.0, 14.0, 17.0, 20.0)  # clock hours, day starts at 08:00
_WINDOW_S = 3600.0
_DAY_S = 86400.0
_START_HOUR = 8.0
_DAY_HOURS = (8.0, 32.0)  # clock-hour domain: one full day from day start


def _shuffled(n: int, r: Stream) -> list[int]:
    """Fisher-Yates over range(n) using only the stream."""
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        j = int(r.f01() * (i + 1))
        order[i], order[j] = order[j], order[i]
    return order


def _emit(gen: Generation, patch: FoodPatch, hour: float) -> None:
    start = (hour - _START_HOUR) * 3600.0
    gen.hazards.append(
        Hazard(patch.x, patch.y, radius=3.5, strength=0.9, start=start, end=start + _WINDOW_S, every=_DAY_S)
    )


def _fixed(r: Stream, gen: Generation) -> None:
    for j, fi in enumerate(_shuffled(len(gen.food), r)[: gen.preset.patrols]):
        hour = _SLOTS[j % len(_SLOTS)] + r.range(-0.5, 0.5)
        _emit(gen, gen.food[fi], hour)


def _sweep(r: Stream, gen: Generation) -> None:
    lo, hi = _DAY_HOURS
    for fi in _shuffled(len(gen.food), r)[: gen.preset.patrols]:
        _emit(gen, gen.food[fi], r.range(lo, hi))


def _circadian(r: Stream, gen: Generation) -> None:
    base = r.range(8.0, 14.0)
    for j, fi in enumerate(_shuffled(len(gen.food), r)[: gen.preset.patrols]):
        _emit(gen, gen.food[fi], base + 6.0 * j + r.range(-0.25, 0.25))


def _regional(r: Stream, gen: Generation) -> None:
    anchor = gen.food[_shuffled(len(gen.food), r)[0]]
    for j in range(gen.preset.patrols):
        hour = _SLOTS[j % len(_SLOTS)] + r.range(-0.5, 0.5)
        _emit(gen, anchor, hour)


STRATEGIES: dict[str, Callable[[Stream, Generation], None]] = {
    "fixed": _fixed,
    "sweep": _sweep,
    "circadian": _circadian,
    "regional": _regional,
}


def validate_strategy(name: str) -> str:
    if name not in STRATEGIES:
        raise ValueError(f"unknown patrol strategy '{name}'; registered: {sorted(STRATEGIES)}")
    return name
