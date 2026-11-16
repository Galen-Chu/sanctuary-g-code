"""TOML output: parses back with tomllib and matches Unbodysoma's key contract."""

from __future__ import annotations

import tomllib

from sanctuary.generate import generate
from sanctuary.presets import PRESETS
from sanctuary.toml_out import scenario_toml


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


def test_golden() -> None:
    """Same seed, byte-identical output, pinned across platforms and versions."""
    from pathlib import Path

    golden = Path(__file__).parent / "golden" / "meadow_seed1.toml"
    text = scenario_toml(generate(1, PRESETS["meadow"]))
    assert text.encode("utf-8") == golden.read_bytes()
