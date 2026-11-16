"""World generation: density fields + rejection sampling + placement rules.

The pipeline distilled from abyssal-garden (docs/DESIGN.md has the full map):

    per-system streams ──► density fields (pure functions of position)
                              │
                              ▼
                   rejection sampling with rules
                   (fertility for food, wetness for water,
                    barren land for permanent hazards)
                              │
                              ▼
                   authored structure on top
                   (shelter beside the best patch,
                    patrols scheduled over patches)

Every random draw comes from a per-system stream, so a stage can be edited
without shifting any other stage's numbers.
"""

from __future__ import annotations

from math import hypot

from .noise import clamp, fbm2
from .presets import Preset
from .rng import Stream, Streams
from .world import FoodPatch, Hazard, Shelter, WaterSource, World

# System ids are a stability contract (docs/DESIGN.md §2): never renumber.
S_TERRAIN = 1  # reserved: terrain fields are pure functions of position
S_FOOD = 2
S_WATER = 3
S_SHELTER = 4
S_HAZARD = 5
S_PATROL = 6

_MARGIN = 2.0
_PATROL_HOURS = (11.0, 14.0, 17.0, 20.0)  # clock hours, day starts at 08:00
_PATROL_WINDOW_S = 3600.0
_DAY_S = 86400.0
_START_HOUR = 8.0


def _fertility(preset: Preset):
    def field(x: float, y: float) -> float:
        return fbm2(x * preset.fertility_scale + 3.7, y * preset.fertility_scale + 9.1, 4)

    return field


def _wetness():
    def field(x: float, y: float) -> float:
        return fbm2(x * 0.045 + 47.3, y * 0.045 + 21.9, 3)

    return field


def _too_close(x: float, y: float, pts: list[tuple[float, float]], gap: float) -> bool:
    g2 = gap * gap
    return any((px - x) * (px - x) + (py - y) * (py - y) < g2 for px, py in pts)


def _sample(
    r: Stream,
    field,
    count: int,
    w: float,
    h: float,
    min_gap: float,
    threshold: float = 0.5,
) -> list[tuple[float, float]]:
    """Rejection-sample ``count`` points from a density field.

    Phase 1 respects ``threshold``; if the field is too barren to satisfy it,
    phase 2 accepts any position. If even the minimum gap cannot be met, the
    gap halves every 20,000 proposals — placement always terminates.
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
        if tries <= 20_000 and field(x, y) < threshold:
            continue
        if _too_close(x, y, pts, gap):
            continue
        pts.append((x, y))
    return pts


def _shuffled(n: int, r: Stream) -> list[int]:
    """Fisher-Yates over range(n) using only the stream."""
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        j = int(r.f01() * (i + 1))
        order[i], order[j] = order[j], order[i]
    return order


def generate(seed: int, preset: Preset) -> World:
    """Generate one world from (seed, preset). Pure: same input, same world."""
    streams = Streams(seed)
    food_r = streams.stream(S_FOOD)
    water_r = streams.stream(S_WATER)
    shelter_r = streams.stream(S_SHELTER)
    hazard_r = streams.stream(S_HAZARD)
    patrol_r = streams.stream(S_PATROL)

    fertility = _fertility(preset)
    wetness = _wetness()
    w, h = preset.width, preset.height

    food_pts = _sample(food_r, fertility, preset.food_count, w, h, preset.min_food_gap)
    water_pts = _sample(water_r, wetness, preset.water_count, w, h, preset.min_water_gap)

    # Shelter beside the most fertile patch, nudged toward the world centre.
    best = max(food_pts, key=lambda p: fertility(p[0], p[1]))
    dx, dy = w / 2 - best[0], h / 2 - best[1]
    dlen = hypot(dx, dy)
    off = shelter_r.range(3.0, 5.0)
    sx = best[0] + (dx / dlen if dlen > 1e-9 else 0.0) * off
    sy = best[1] + (dy / dlen if dlen > 1e-9 else 0.0) * off
    shelter = Shelter(clamp(sx, _MARGIN, w - _MARGIN), clamp(sy, _MARGIN, h - _MARGIN))

    # Permanent hazards: barren ground, clear of water and the shelter.
    hazards: list[Hazard] = []
    for _ in range(preset.permanent_hazards):
        placed = _place_permanent(hazard_r, fertility, w, h, water_pts, shelter, hazards, preset.hazard_clearance)
        if placed is not None:
            hazards.append(placed)

    # Patrols: daily visitors on distinct food patches, spread across the day.
    for j, fi in enumerate(_shuffled(len(food_pts), patrol_r)[: preset.patrols]):
        hour = _PATROL_HOURS[j % len(_PATROL_HOURS)] + patrol_r.range(-0.5, 0.5)
        start = (hour - _START_HOUR) * 3600.0
        px, py = food_pts[fi]
        hazards.append(
            Hazard(px, py, radius=3.5, strength=0.9, start=start, end=start + _PATROL_WINDOW_S, every=_DAY_S)
        )

    return World(
        name=f"{preset.name}_s{seed}",
        preset=preset.name,
        preset_version=preset.version,
        seed=seed,
        width=w,
        height=h,
        start=(shelter.x, shelter.y),  # the organism wakes at home
        food=tuple(FoodPatch(x, y, regrow_per_hour=preset.regrow_per_hour) for x, y in food_pts),
        water=tuple(WaterSource(x, y) for x, y in water_pts),
        shelters=(shelter,),
        hazards=tuple(hazards),
    )


def _place_permanent(
    r: Stream,
    fertility,
    w: float,
    h: float,
    water_pts: list[tuple[float, float]],
    shelter: Shelter,
    existing: list[Hazard],
    clearance: float,
) -> Hazard | None:
    for _ in range(4_000):
        x = r.range(_MARGIN, w - _MARGIN)
        y = r.range(_MARGIN, h - _MARGIN)
        if fertility(x, y) > 0.45:  # want barren ground
            continue
        if hypot(x - shelter.x, y - shelter.y) < clearance + shelter.radius + 2.0:
            continue
        if any(hypot(x - wx, y - wy) < clearance for wx, wy in water_pts):
            continue
        if any(hypot(x - e.x, y - e.y) < clearance for e in existing):
            continue
        return Hazard(x, y, radius=r.range(2.0, 3.5), strength=0.9)
    return None
