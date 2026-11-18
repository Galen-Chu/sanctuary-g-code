"""Composable systems: registry contract, composition validation, contraction."""

from __future__ import annotations

import dataclasses

import pytest

from sanctuary.generate import generate
from sanctuary.presets import PRESETS, Preset
from sanctuary.systems import CANONICAL_ORDER, SYSTEMS, canonical_selection, validate_composition


def test_registry_matches_canonical_order() -> None:
    assert tuple(SYSTEMS) == CANONICAL_ORDER == ("food", "water", "shelter", "hazard-permanent", "hazard-patrol")


def test_stream_ids_are_the_stability_contract() -> None:
    """DESIGN section 2 table: terrain id 1 reserved; these five never renumber."""
    assert [SYSTEMS[name].stream_id for name in CANONICAL_ORDER] == [2, 3, 4, 5, 6]
    assert len({s.stream_id for s in SYSTEMS.values()}) == len(SYSTEMS)


def test_preset_default_composition_is_canonical() -> None:
    bare = Preset(name="x", description="", width=10.0, height=10.0, food_count=1, water_count=1)
    assert bare.systems == CANONICAL_ORDER


def test_validation_rejects_unknown_and_empty() -> None:
    with pytest.raises(ValueError, match="unknown systems"):
        validate_composition(("food", "seasons"))
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
