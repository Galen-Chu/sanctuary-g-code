"""Composable generation systems: the registered vocabulary an archetype selects from.

DESIGN section 3's composable-systems direction, landed with its two hard
rules intact: reorganizing code must not move a single draw (byte-stability,
verified by goldens), and contraction comes before expansion (an archetype
selects a subsequence of the canonical order — kelp-basin now drops
permanent hazards structurally, not via a zero parameter).

Interface (DESIGN open question 4, v1): a system is a function over a
mutable ``Generation`` accumulation. It draws only from its own per-system
stream, reads what earlier systems produced, and appends entities. Because
streams are independent, cross-system order never affects bytes; the
canonical order exists for data dependencies (shelter and patrols need
food), which each system declares and composition validation enforces.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from math import hypot, sin, tau

from .noise import clamp, fbm2
from .presets import Preset
from .rng import Stream, Streams
from .strategies import STRATEGIES
from .world import FoodPatch, Hazard, Season, Shelter, WaterSource

# System ids are a stability contract (docs/DESIGN.md §2): never renumber.
S_TERRAIN = 1  # pure functions of position: the stream stays unused
S_FOOD = 2
S_WATER = 3
S_SHELTER = 4
S_HAZARD = 5
S_PATROL = 6
S_SEASONS = 7  # the season plan is preset math today; the stream waits for
#               per-patch asynchrony (if ever) to need draws

_MARGIN = 2.0

# Season names for the default four-phase cycle: the sinusoid starts at its
# minimum (winter = leanest), peaks in summer, and means exactly 1.0.
_SEASON_NAMES = ("winter", "spring", "summer", "autumn")


@dataclass
class Generation:
    """The mutable accumulation one world is built in.

    ``fertility`` / ``wetness`` are pure functions of position (plus preset
    constants); systems read them freely — they never draw. ``passable`` is
    ``None`` unless the terrain system is in the composition.
    """

    seed: int
    preset: Preset
    streams: Streams
    fertility: Callable[[float, float], float]
    wetness: Callable[[float, float], float]
    passable: Callable[[float, float], bool] | None = None
    food: list[FoodPatch] = field(default_factory=list)
    water: list[WaterSource] = field(default_factory=list)
    shelters: list[Shelter] = field(default_factory=list)
    hazards: list[Hazard] = field(default_factory=list)
    seasons: list[Season] = field(default_factory=list)


@dataclass(frozen=True)
class System:
    """One registered generation system: stream owner + entity producer."""

    name: str
    stream_id: int
    apply: Callable[[Generation], None]
    needs: frozenset[str] = frozenset()  # systems that must run before this one


def _too_close(x: float, y: float, pts: list[tuple[float, float]], gap: float) -> bool:
    g2 = gap * gap
    return any((px - x) * (px - x) + (py - y) * (py - y) < g2 for px, py in pts)


def _sample(
    r: Stream,
    field_fn: Callable[[float, float], float],
    count: int,
    w: float,
    h: float,
    min_gap: float,
    threshold: float = 0.5,
    passable: Callable[[float, float], bool] | None = None,
) -> list[tuple[float, float]]:
    """Rejection-sample ``count`` points from a density field.

    Phase 1 respects ``threshold``; if the field is too barren to satisfy it,
    phase 2 accepts any position. If even the minimum gap cannot be met, the
    gap halves every 20,000 proposals — placement always terminates.

    ``passable`` (terrain system) is a **hard** constraint: it is never
    relaxed by the phase-2 fallback, because plants cannot root on impassable
    ground no matter how contested the map is. The density threshold stays the
    soft, relaxable one. ``passable=None`` (no terrain system) changes nothing.
    """
    pts: list[tuple[float, float]] = []
    tries = 0
    gap = min_gap
    while len(pts) < count:
        tries += 1
        if tries % 20_000 == 0:
            gap *= 0.5
        x = r.range(_MARGIN, w - _MARGIN)
        y = r.range(_MARGIN, h - _MARGIN)
        # Cheap rejections first: all predicates must pass, so their order
        # changes nothing about which proposals are accepted -- only how
        # many fbm evaluations the rejected ones cost.
        if _too_close(x, y, pts, gap):
            continue
        if passable is not None and not passable(x, y):
            continue
        if tries <= 20_000 and field_fn(x, y) < threshold:
            continue
        pts.append((x, y))
    return pts


def _schedule_patrols(gen: Generation) -> None:
    """Dispatch to the archetype's patrol strategy (strategies.py registry)."""
    r = gen.streams.stream(S_PATROL)
    STRATEGIES[gen.preset.patrol_strategy](r, gen)


def _elevation_field(preset: Preset) -> Callable[[float, float], float]:
    """Elevation is a pure function of position (abyssal domain-offset
    convention: fresh offsets keep it independent of fertility and wetness)."""

    def elevation(x: float, y: float) -> float:
        return fbm2(x * preset.terrain_scale + 113.7, y * preset.terrain_scale + 61.3, 4)

    return elevation


def passable_fn(preset: Preset) -> Callable[[float, float], bool]:
    """The terrain passability predicate — public because the statistics
    layer grid-estimates the impassable fraction with the very same
    function the generator rejects proposals with."""

    elevation = _elevation_field(preset)

    def passable(x: float, y: float) -> bool:
        return elevation(x, y) < preset.impassable_threshold

    return passable


def _build_terrain(gen: Generation) -> None:
    """Elevation field: ground above ``impassable_threshold`` cannot host
    plants. The field is pure preset math — the reserved stream id 1 stays
    unused (DESIGN §2). Food placement treats passability as a hard
    constraint (see ``_sample``)."""
    gen.passable = passable_fn(gen.preset)


def _place_food(gen: Generation) -> None:
    r = gen.streams.stream(S_FOOD)
    pts = _sample(
        r,
        gen.fertility,
        gen.preset.food_count,
        gen.preset.width,
        gen.preset.height,
        gen.preset.min_food_gap,
        passable=gen.passable,
    )
    gen.food.extend(FoodPatch(x, y, regrow_per_hour=gen.preset.regrow_per_hour) for x, y in pts)


def _place_water(gen: Generation) -> None:
    r = gen.streams.stream(S_WATER)
    pts = _sample(r, gen.wetness, gen.preset.water_count, gen.preset.width, gen.preset.height, gen.preset.min_water_gap)
    gen.water.extend(WaterSource(x, y) for x, y in pts)


def _place_shelter(gen: Generation) -> None:
    """Beside the most fertile patch, nudged toward the world centre."""
    r = gen.streams.stream(S_SHELTER)
    best = max(gen.food, key=lambda f: gen.fertility(f.x, f.y))
    w, h = gen.preset.width, gen.preset.height
    dx, dy = w / 2 - best.x, h / 2 - best.y
    dlen = hypot(dx, dy)
    off = r.range(3.0, 5.0)
    sx = best.x + (dx / dlen if dlen > 1e-9 else 0.0) * off
    sy = best.y + (dy / dlen if dlen > 1e-9 else 0.0) * off
    gen.shelters.append(Shelter(clamp(sx, _MARGIN, w - _MARGIN), clamp(sy, _MARGIN, h - _MARGIN)))


def _place_permanent(gen: Generation) -> None:
    """Permanent hazards: barren ground, clear of water and the shelter."""
    r = gen.streams.stream(S_HAZARD)
    w, h = gen.preset.width, gen.preset.height
    clearance = gen.preset.hazard_clearance
    water_pts = [(s.x, s.y) for s in gen.water]
    shelter = gen.shelters[0] if gen.shelters else None
    for _ in range(gen.preset.permanent_hazards):
        placed = _try_place_permanent(r, gen.fertility, w, h, water_pts, shelter, gen.hazards, clearance)
        if placed is not None:
            gen.hazards.append(placed)


def _try_place_permanent(
    r: Stream,
    fertility: Callable[[float, float], float],
    w: float,
    h: float,
    water_pts: list[tuple[float, float]],
    shelter: Shelter | None,
    existing: list[Hazard],
    clearance: float,
) -> Hazard | None:
    for _ in range(4_000):
        x = r.range(_MARGIN, w - _MARGIN)
        y = r.range(_MARGIN, h - _MARGIN)
        # Cheap rejections first (see _sample): same accepts, fewer fbm calls.
        if shelter is not None and hypot(x - shelter.x, y - shelter.y) < clearance + shelter.radius + 2.0:
            continue
        if any(hypot(x - wx, y - wy) < clearance for wx, wy in water_pts):
            continue
        if any(hypot(x - e.x, y - e.y) < clearance for e in existing):
            continue
        if fertility(x, y) > 0.45:  # want barren ground
            continue
        return Hazard(x, y, radius=r.range(2.0, 3.5), strength=0.9)
    return None


def _plan_seasons(gen: Generation) -> None:
    """A global seasonal regrowth cycle (Phase 3).

    Season ``k``'s multiplier is ``1 + amplitude · sin(2πk/n − π/2)``: the
    cycle starts at its leanest phase, peaks at ``1 + amplitude``, and means
    exactly 1.0 over one cycle — no net resource drift. The standard four
    phases carry the calendar names (winter = leanest → autumn = falling);
    other counts use neutral names. Pure preset math: stream id 7 stays
    unused until per-patch phase asynchrony (if ever) needs draws.
    """
    n = gen.preset.season_count
    a = gen.preset.season_amplitude
    duration = gen.preset.season_cycle_h / n
    phase0 = -tau / 4.0  # −π/2: season 0 sits at the sinusoid's minimum
    for k in range(n):
        multiplier = 1.0 + a * sin(tau * k / n + phase0)
        name = _SEASON_NAMES[k] if n == 4 else f"season{k + 1}"
        gen.seasons.append(Season(name=name, duration_h=duration, regrow_multiplier=round(multiplier, 6)))


# Canonical order: a topological order of the dependency graph. Execution is
# always this order restricted to the archetype's selection.
SYSTEMS: dict[str, System] = {
    "terrain": System("terrain", S_TERRAIN, _build_terrain),
    "food": System("food", S_FOOD, _place_food),
    "water": System("water", S_WATER, _place_water),
    "shelter": System("shelter", S_SHELTER, _place_shelter, frozenset({"food"})),
    "hazard-permanent": System("hazard-permanent", S_HAZARD, _place_permanent),
    "hazard-patrol": System("hazard-patrol", S_PATROL, _schedule_patrols, frozenset({"food"})),
    "seasons": System("seasons", S_SEASONS, _plan_seasons, frozenset({"food"})),
}

CANONICAL_ORDER: tuple[str, ...] = tuple(SYSTEMS)


def canonical_selection(names: tuple[str, ...] | frozenset[str]) -> tuple[str, ...]:
    """The selection in canonical order (input order is never significant)."""
    return tuple(name for name in CANONICAL_ORDER if name in set(names))


def validate_composition(names: tuple[str, ...] | frozenset[str]) -> tuple[str, ...]:
    """Validate an archetype's composition and return it in canonical order."""
    selection = set(names)
    if not selection:
        raise ValueError("an archetype must select at least one system")
    unknown = selection - set(SYSTEMS)
    if unknown:
        raise ValueError(f"unknown systems {sorted(unknown)}; registered: {list(CANONICAL_ORDER)}")
    for name in canonical_selection(tuple(selection)):
        missing = SYSTEMS[name].needs - selection
        if missing:
            raise ValueError(f"system '{name}' requires {sorted(missing)} in the composition")
    return canonical_selection(tuple(selection))
