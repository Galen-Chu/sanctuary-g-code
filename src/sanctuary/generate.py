"""World generation: run an archetype's systems over a fresh accumulation.

The pipeline distilled from abyssal-garden (docs/DESIGN.md §3) lives in
``systems.py`` as five registered systems; ``generate`` validates the
archetype's composition, runs it in canonical order, and assembles the
immutable ``World``. Pure: same (seed, preset), same world, same bytes —
the per-system streams mean one system can be added, dropped, or edited
without shifting any other system's draws.
"""

from __future__ import annotations

from collections.abc import Callable

from .noise import fbm2
from .presets import Preset
from .rng import Streams
from .systems import SYSTEMS, Generation, validate_composition
from .world import World

Field = Callable[[float, float], float]


def _fertility(preset: Preset) -> Field:
    def field(x: float, y: float) -> float:
        return fbm2(x * preset.fertility_scale + 3.7, y * preset.fertility_scale + 9.1, 4)

    return field


def _wetness() -> Field:
    def field(x: float, y: float) -> float:
        return fbm2(x * 0.045 + 47.3, y * 0.045 + 21.9, 3)

    return field


def generate(seed: int, preset: Preset) -> World:
    """Generate one world from (seed, preset). Pure: same input, same world."""
    selection = validate_composition(preset.systems)
    gen = Generation(
        seed=seed,
        preset=preset,
        streams=Streams(seed),
        fertility=_fertility(preset),
        wetness=_wetness(),
    )
    for name in selection:
        SYSTEMS[name].apply(gen)

    # The organism wakes at home; a shelterless archetype starts at the centre.
    if gen.shelters:
        start = (gen.shelters[0].x, gen.shelters[0].y)
    else:
        start = (preset.width / 2, preset.height / 2)
    return World(
        name=f"{preset.name}_s{seed}",
        preset=preset.name,
        preset_version=preset.version,
        seed=seed,
        width=preset.width,
        height=preset.height,
        start=start,
        systems=selection,
        food=tuple(gen.food),
        water=tuple(gen.water),
        shelters=tuple(gen.shelters),
        hazards=tuple(gen.hazards),
    )
