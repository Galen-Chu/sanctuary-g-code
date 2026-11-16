"""Named world presets: the knobs a scenario author turns.

A preset fixes every structural parameter of a world; the seed then decides
everything else. Changing a preset's numbers changes the *class* of worlds it
produces (and invalidates nothing — worlds carry their preset name and seed
for reproduction).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    width: float
    height: float
    food_count: int
    water_count: int
    shelter_count: int = 1
    permanent_hazards: int = 1
    patrols: int = 2  # scheduled predators, each visiting one food patch daily
    fertility_scale: float = 0.06  # noise scale of the fertility field (1/cells)
    regrow_per_hour: float = 0.1
    min_food_gap: float = 5.0  # minimum distance between food patches (cells)
    min_water_gap: float = 6.0
    hazard_clearance: float = 3.0  # permanent hazards keep this far from water/shelter
    # Provenance contract (docs/DESIGN.md §2 item 5): bump when any number or
    # generation semantic of this preset changes. Old worlds record the revision
    # that made them; regenerating one after a bump means checking out that commit.
    version: int = 1


PRESETS: dict[str, Preset] = {
    # Balanced default, closest in spirit to Unbodysoma's hand-authored grid_72h.
    "meadow": Preset(
        name="meadow",
        description=(
            "Balanced foraging world: five patches, two springs, one shelter, one barren danger zone, two daily patrols"
        ),
        width=20.0,
        height=20.0,
        food_count=5,
        water_count=2,
    ),
    # Rich, clustered food (fine fertility scale -> tight clusters), heavier predation.
    # Named for the source project's kelp basin.
    "kelp-basin": Preset(
        name="kelp-basin",
        description=(
            "Dense clustered food, four daily patrols, no permanent hazard — pressure comes from visitors, not terrain"
        ),
        width=24.0,
        height=24.0,
        food_count=7,
        water_count=2,
        permanent_hazards=0,
        patrols=4,
        fertility_scale=0.10,
        regrow_per_hour=0.14,
    ),
    # Scarce water, two barren danger zones: temperature and thirst dominate.
    "dryland": Preset(
        name="dryland",
        description="Scarce water and two permanent danger zones; food is neither dense nor fast to regrow",
        width=22.0,
        height=22.0,
        food_count=4,
        water_count=1,
        permanent_hazards=2,
        patrols=1,
        fertility_scale=0.05,
        regrow_per_hour=0.08,
        min_food_gap=6.0,
    ),
}
