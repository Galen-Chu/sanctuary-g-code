"""World description: field-compatible mirrors of Unbodysoma's world dataclasses.

Mirrored, not imported: Sanctuary's core has zero dependencies and Unbodysoma
stays unaware of Sanctuary. ``toml_out`` emits exactly the keys Unbodysoma's
scenario loader accepts (``FoodPatch`` / ``WaterSource`` / ``Shelter`` /
``Hazard`` in ``unbodysoma/world/grid.py``), so the mirror must track any
change there — the round-trip test reads a generated file back with
``tomllib`` and checks the structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class FoodPatch:
    """Food at ``(x, y)``; regrows after being eaten (Unbodysoma: marginal value theorem)."""

    x: float
    y: float
    capacity: float = 1.0
    regrow_per_hour: float = 0.25


@dataclass(frozen=True)
class WaterSource:
    """Water at ``(x, y)`` that never runs out (a spring, a stream)."""

    x: float
    y: float


@dataclass(frozen=True)
class Shelter:
    """A refuge: inside ``radius`` the temperature is buffered and hazards cannot reach."""

    x: float
    y: float
    radius: float = 1.0
    insulation: float = 0.8


@dataclass(frozen=True)
class Hazard:
    """A danger zone: threat ``strength`` at the centre, fading to 0 at ``radius``.

    Active during ``[start, end)``; with ``every`` finite the window repeats
    (e.g. a predator that visits daily). ``inf`` defaults mean "always on".
    """

    x: float
    y: float
    radius: float = 2.0
    strength: float = 0.9
    start: float = 0.0
    end: float = inf
    every: float = inf

    @property
    def scheduled(self) -> bool:
        return self.end != inf


@dataclass(frozen=True)
class Season:
    """One phase of the seasonal resource cycle.

    For ``duration_h`` hours, every food patch's regrowth rate scales by
    ``regrow_multiplier`` (1.0 = nominal). The cycle repeats every
    ``sum(duration_h)`` hours for as long as the simulation runs.
    """

    name: str
    duration_h: float
    regrow_multiplier: float


@dataclass(frozen=True)
class World:
    """A complete generated world plus the bookkeeping to reproduce it."""

    name: str
    preset: str
    preset_version: int
    seed: int
    width: float
    height: float
    start: tuple[float, float]
    systems: tuple[str, ...] = ()  # composition provenance; () = legacy, assume all
    food: tuple[FoodPatch, ...] = ()
    water: tuple[WaterSource, ...] = ()
    shelters: tuple[Shelter, ...] = ()
    hazards: tuple[Hazard, ...] = ()
    seasons: tuple[Season, ...] = ()  # empty = aseasonal (legacy worlds)
