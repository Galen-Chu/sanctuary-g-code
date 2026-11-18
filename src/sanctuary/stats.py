"""Statistical fingerprints: distribution-level acceptance across seeds.

A single world satisfies invariants (test_generate); a *class* of worlds
satisfies statistics. The fingerprint summarizes one preset over seeds
``seed..seed+count-1`` (the same derivation idiom as population mode) and is
the semantic basis of the future world library: an archetype's fingerprint
is what specimen index cards store (BACKLOG section 1).

Bounds are calibrated from the generation rules' own theory -- never tuned
until tests go green:

- Nearest-resource distance: proposals are uniform in the effective area
  ``A_eff = (W-4) * (H-4)`` (the 2-cell margin), so for ``n`` points
  ``P(d > r) = exp(-n * pi * r^2 / A_eff)`` and the median is
  ``sqrt(ln 2 * A_eff / (pi * n))``. Finite n and window edges inflate the
  true median ~10% (unit square: 0.470 theory vs 0.511 exact); field
  clustering (wetness correlation) can inflate more. The band factors
  absorb both, deliberately wide until the theory sharpens.
- Hazard coverage: independent random disks give ``1 - prod(1 - a_i / A)``.
- Shelter offset: uniform 3..5 cells toward the centre from the best food
  patch (generate.py), so the shelter-food median sits in that range.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median

from .presets import Preset
from .world import World

# Band factors around the theory centres. Tighten only with a sharpened
# theory, never by observing where a test happens to sit (DESIGN section 5).
WATER_BAND_FACTOR = (0.5, 2.0)
COVERAGE_BAND_FACTOR = (0.5, 1.75)
SHELTER_FOOD_BAND = (2.5, 5.5)  # offset range 3..5 + clamp/nearest-tie slack

_PERMANENT_DISK_E = math.pi * 7.75  # E[pi r^2] for r ~ U(2.0, 3.5)
_PATROL_RADIUS = 3.5


def poisson_median_nearest(effective_area: float, n: int) -> float:
    """Median distance from a query point to the nearest of ``n`` ~uniform points."""
    return math.sqrt(math.log(2.0) * effective_area / (math.pi * n))


def expected_hazard_coverage(preset: Preset) -> float:
    """Expected world-area fraction covered by independent random hazard disks."""
    area = preset.width * preset.height
    uncovered = (1.0 - _PERMANENT_DISK_E / area) ** max(preset.permanent_hazards, 0)
    uncovered *= (1.0 - math.pi * _PATROL_RADIUS**2 / area) ** preset.patrols
    return 1.0 - uncovered


def nearest_distance(x: float, y: float, points: tuple[tuple[float, float], ...]) -> float:
    """Distance from ``(x, y)`` to the nearest of ``points`` (inf when empty)."""
    return min((math.hypot(px - x, py - y) for px, py in points), default=math.inf)


def food_water_distances(world: World) -> tuple[float, ...]:
    """Per food patch: distance to the nearest water source."""
    water = tuple((w.x, w.y) for w in world.water)
    return tuple(nearest_distance(f.x, f.y, water) for f in world.food)


def shelter_food_distance(world: World) -> float:
    """Distance from the shelter to the nearest food patch."""
    food = tuple((f.x, f.y) for f in world.food)
    return nearest_distance(world.shelters[0].x, world.shelters[0].y, food)


def shelter_water_distance(world: World) -> float:
    """Distance from the shelter to the nearest water source."""
    water = tuple((w.x, w.y) for w in world.water)
    return nearest_distance(world.shelters[0].x, world.shelters[0].y, water)


def hazard_coverage(world: World, step: float = 0.5) -> float:
    """Fraction of the world covered by at least one hazard disk.

    Deterministic grid estimate (cell centres, no RNG), so the same world
    always yields the same number.
    """
    hazards = tuple((h.x, h.y, h.radius) for h in world.hazards)
    if not hazards:
        return 0.0
    inside = 0
    total = 0
    ny = int(world.height / step)
    nx = int(world.width / step)
    for iy in range(ny):
        y = (iy + 0.5) * step
        for ix in range(nx):
            x = (ix + 0.5) * step
            total += 1
            if any(math.hypot(x - hx, y - hy) <= r for hx, hy, r in hazards):
                inside += 1
    return inside / total


def patrol_clock_hours(world: World) -> tuple[float, ...]:
    """Clock hours (day starts 08:00) of the scheduled hazards, in draw order."""
    return tuple(h.start / 3600.0 + 8.0 for h in world.hazards if h.scheduled)


@dataclass(frozen=True)
class Fingerprint:
    """Distribution summary of one preset across ``seeds``."""

    preset: str
    seed: int
    count: int
    water_gap_food_median: float
    shelter_food_median: float
    shelter_water_median: float
    hazard_coverage_mean: float


def format_fingerprint(fp: Fingerprint, preset: Preset) -> str:
    """Human-readable fingerprint with theory centres and bands beside it."""
    center_water = poisson_median_nearest((preset.width - 4) * (preset.height - 4), preset.water_count)
    center_cov = expected_hazard_coverage(preset)
    wlo, whi = WATER_BAND_FACTOR
    clo, chi = COVERAGE_BAND_FACTOR
    lines = [
        f"{fp.preset} across {fp.count} seeds ({fp.seed}..{fp.seed + fp.count - 1}):",
        f"  water-gap/food median  {fp.water_gap_food_median:7.2f}  center {center_water:.2f},"
        f" band [{wlo * center_water:.2f}, {whi * center_water:.2f}]",
        f"  shelter-water median   {fp.shelter_water_median:7.2f}  same center/band",
        f"  shelter-food median    {fp.shelter_food_median:7.2f}  offset 3..5, band {SHELTER_FOOD_BAND}",
        f"  hazard coverage mean   {fp.hazard_coverage_mean:7.3f}  center {center_cov:.3f},"
        f" band [{clo * center_cov:.3f}, {chi * center_cov:.3f}]",
    ]
    return "\n".join(lines)


def fingerprint(seed: int, preset: Preset, count: int = 100) -> Fingerprint:
    """Summarize ``preset`` over worlds ``seed..seed+count-1``."""
    from .generate import generate

    water_gaps: list[float] = []
    shelter_food: list[float] = []
    shelter_water: list[float] = []
    coverages: list[float] = []
    for i in range(count):
        world = generate(seed + i, preset)
        water_gaps.append(median(food_water_distances(world)))
        shelter_food.append(shelter_food_distance(world))
        shelter_water.append(shelter_water_distance(world))
        coverages.append(hazard_coverage(world))
    return Fingerprint(
        preset=preset.name,
        seed=seed,
        count=count,
        water_gap_food_median=median(water_gaps),
        shelter_food_median=median(shelter_food),
        shelter_water_median=median(shelter_water),
        hazard_coverage_mean=sum(coverages) / len(coverages),
    )
