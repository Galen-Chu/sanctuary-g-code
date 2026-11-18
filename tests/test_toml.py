"""TOML output: parses back with tomllib and matches Unbodysoma's key contract."""

from __future__ import annotations

import tomllib

import pytest

from sanctuary.generate import generate
from sanctuary.presets import PRESETS
from sanctuary.toml_out import scenario_toml
from sanctuary.world import World


def test_toml_capability_raises_for_unsupported_system() -> None:
    """Adapter capability (DESIGN section 4): unknown vocabulary fails loudly."""
    world = World(
        name="t",
        preset="t",
        preset_version=1,
        seed=0,
        width=10.0,
        height=10.0,
        start=(5.0, 5.0),
        systems=("food", "seasons"),
    )
    with pytest.raises(ValueError, match="cannot express"):
        scenario_toml(world)


def test_roundtrip_structure() -> None:
    text = scenario_toml(generate(2, PRESETS["meadow"]))
    data = tomllib.loads(text)

    assert set(data) == {"scenario", "organism", "world", "observe"}
    scenario = data["scenario"]
    assert set(scenario) == {"name", "description", "duration_h", "seed", "base_dt"}
    assert scenario["seed"] == 2
    assert data["organism"] == {"preset": "grid"}

    world = data["world"]
    assert set(world) == {"width", "height", "start", "food", "water", "shelters", "hazards"}
    assert len(world["start"]) == 2

    assert len(world["food"]) == PRESETS["meadow"].food_count
    for patch in world["food"]:
        assert set(patch) <= {"x", "y", "capacity", "regrow_per_hour"}
        assert {"x", "y", "regrow_per_hour"} <= set(patch)
    for spring in world["water"]:
        assert set(spring) == {"x", "y"}
    for shelter in world["shelters"]:
        assert set(shelter) == {"x", "y", "radius", "insulation"}
    for hazard in world["hazards"]:
        assert set(hazard) <= {"x", "y", "radius", "strength", "start", "end", "every"}
        assert {"x", "y", "radius", "strength"} <= set(hazard)


def test_permanent_hazard_omits_schedule() -> None:
    """TOML has no infinity literal: always-on hazards omit start/end/every."""
    text = scenario_toml(generate(0, PRESETS["meadow"]))
    data = tomllib.loads(text)
    scheduled = [h for h in data["world"]["hazards"] if "start" in h]
    assert len(scheduled) == PRESETS["meadow"].patrols


def test_organism_seed_override() -> None:
    text = scenario_toml(generate(5, PRESETS["meadow"]), organism_seed=99)
    assert tomllib.loads(text)["scenario"]["seed"] == 99


def test_provenance_header() -> None:
    """The header carries the provenance stamp: preset@version, seed, reproduce line."""
    text = scenario_toml(generate(1, PRESETS["meadow"]))
    assert "preset=meadow@1" in text.splitlines()[0]
    assert "Reproduce: sanctuary --seed 1 --preset meadow" in text.splitlines()[1]


def test_golden() -> None:
    """Same seed, byte-identical output, pinned across platforms and versions."""
    from pathlib import Path

    golden = Path(__file__).parent / "golden" / "meadow_seed1.toml"
    text = scenario_toml(generate(1, PRESETS["meadow"]))
    assert text.encode("utf-8") == golden.read_bytes()
