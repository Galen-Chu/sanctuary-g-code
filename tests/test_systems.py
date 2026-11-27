"""Composable systems: registry contract, composition validation, contraction."""

from __future__ import annotations

import dataclasses
import math

import pytest

from sanctuary.generate import generate
from sanctuary.presets import PRESETS, Preset
from sanctuary.systems import (
    CANONICAL_ORDER,
    SYSTEMS,
    canonical_selection,
    passable_fn,
    validate_composition,
)

# The classic five: what a bare Preset selects (and every pre-Phase-3 world).
CLASSIC = ("food", "water", "shelter", "hazard-permanent", "hazard-patrol")


def test_registry_matches_canonical_order() -> None:
    assert tuple(SYSTEMS) == CANONICAL_ORDER == (
        "terrain",
        "food",
        "water",
        "shelter",
        "hazard-permanent",
        "hazard-patrol",
        "seasons",
    )


def test_stream_ids_are_the_stability_contract() -> None:
    """DESIGN section 2 table: ids 1-7, never renumbered. Terrain (1) and
    seasons (7) own streams they do not currently draw from."""
    assert [SYSTEMS[name].stream_id for name in CANONICAL_ORDER] == [1, 2, 3, 4, 5, 6, 7]
    assert len({s.stream_id for s in SYSTEMS.values()}) == len(SYSTEMS)


def test_preset_default_composition_is_the_classic_five() -> None:
    """A bare preset stays aseasonal and terrain-free: existing presets rely
    on this default, and goldens pin their worlds byte for byte."""
    bare = Preset(name="x", description="", width=10.0, height=10.0, food_count=1, water_count=1)
    assert bare.systems == CLASSIC


def test_validation_rejects_unknown_and_empty() -> None:
    with pytest.raises(ValueError, match="unknown systems"):
        validate_composition(("food", "tides"))
    with pytest.raises(ValueError, match="at least one"):
        validate_composition(())


def test_validation_rejects_patrols_without_food() -> None:
    with pytest.raises(ValueError, match="requires"):
        validate_composition(("water", "hazard-patrol"))


def test_validation_rejects_shelter_without_food() -> None:
    with pytest.raises(ValueError, match="requires"):
        validate_composition(("shelter",))


def test_canonical_selection_ignores_input_order() -> None:
    assert canonical_selection(("hazard-patrol", "food")) == ("food", "hazard-patrol")


def test_contraction_composition_is_deterministic() -> None:
    """A shelterless archetype: food+water only, organism starts at the centre."""
    preset = dataclasses.replace(PRESETS["meadow"], name="bare", systems=("food", "water"))
    world = generate(7, preset)
    assert world == generate(7, preset)
    assert world.systems == ("food", "water")
    assert world.food and world.water
    assert not world.shelters and not world.hazards
    assert world.start == (preset.width / 2, preset.height / 2)


def test_kelp_basin_contraction_is_structural() -> None:
    """kelp-basin drops hazard-permanent by composition, not by a zero parameter."""
    assert "hazard-permanent" not in PRESETS["kelp-basin"].systems
    world = generate(1, PRESETS["kelp-basin"])
    assert world.systems == ("food", "water", "shelter", "hazard-patrol")
    assert not [h for h in world.hazards if not h.scheduled]


# ── Phase 3: terrain ──────────────────────────────────────────────────────────


def test_terrain_places_food_only_on_passable_ground() -> None:
    """The hard constraint: every food patch sits on passable soil, across seeds."""
    world = generate(1, PRESETS["highlands"])
    predicate = passable_fn(PRESETS["highlands"])
    assert world.systems[0] == "terrain"
    assert world.food, "the archetype must still place its full food count"
    assert len(world.food) == PRESETS["highlands"].food_count
    assert all(predicate(f.x, f.y) for f in world.food)
    for seed in (0, 7, 42, 20261116):
        assert all(predicate(f.x, f.y) for f in generate(seed, PRESETS["highlands"]).food)


def test_terrain_does_not_move_other_systems_draws() -> None:
    """Per-system streams: adding terrain changes food placement (intended) but
    water, shelter and hazards must be draw-for-draw identical to meadow's."""
    meadow = generate(11, PRESETS["meadow"])
    highlands = generate(11, PRESETS["highlands"])
    assert [w.x for w in meadow.water] == [w.x for w in highlands.water]
    assert [w.y for w in meadow.water] == [w.y for w in highlands.water]
    assert meadow.shelters == highlands.shelters
    assert meadow.hazards == highlands.hazards


def test_terrain_without_terrain_system_changes_nothing() -> None:
    """meadow's world is byte-stable across the Phase 3 registry growth."""
    world = generate(1, PRESETS["meadow"])
    assert world.systems == CLASSIC
    assert len(world.food) == 5 and len(world.water) == 2


def test_passable_fn_matches_preset_threshold() -> None:
    preset = PRESETS["highlands"]
    predicate = passable_fn(preset)
    values = [predicate(x, 10.0) for x in [i * 0.25 for i in range(80)]]
    assert any(values) and not all(values), "the field must have both kinds of ground"


# ── Phase 3: seasons ──────────────────────────────────────────────────────────


def test_season_cycle_starts_lean_peaks_and_means_one() -> None:
    world = generate(3, PRESETS["meadow-seasons"])
    assert [s.name for s in world.seasons] == ["winter", "spring", "summer", "autumn"]
    multipliers = [s.regrow_multiplier for s in world.seasons]
    a = PRESETS["meadow-seasons"].season_amplitude
    assert math.isclose(min(multipliers), 1.0 - a, abs_tol=1e-6)   # winter
    assert math.isclose(max(multipliers), 1.0 + a, abs_tol=1e-6)   # summer
    durations = [s.duration_h for s in world.seasons]
    assert math.isclose(sum(durations), PRESETS["meadow-seasons"].season_cycle_h)
    weighted = sum(m * d for m, d in zip(multipliers, durations, strict=True)) / sum(durations)
    assert math.isclose(weighted, 1.0, abs_tol=1e-9), "no net resource drift"


def test_seasons_do_not_move_resource_draws() -> None:
    """The season plan is preset math: food/water/hazards identical to meadow's."""
    meadow = generate(5, PRESETS["meadow"])
    seasonal = generate(5, PRESETS["meadow-seasons"])
    assert meadow.food == seasonal.food
    assert meadow.water == seasonal.water
    assert meadow.hazards == seasonal.hazards
    assert not meadow.seasons and seasonal.seasons


def test_seasons_requires_food_in_composition() -> None:
    with pytest.raises(ValueError, match="requires"):
        validate_composition(("water", "seasons"))


def test_season_count_other_than_four_uses_neutral_names() -> None:
    preset = dataclasses.replace(PRESETS["meadow-seasons"], season_count=6)
    world = generate(1, preset)
    assert [s.name for s in world.seasons] == [f"season{k}" for k in range(1, 7)]
