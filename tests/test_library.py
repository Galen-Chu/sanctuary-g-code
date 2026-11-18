"""Library artifacts: deterministic JSON index and specimen cards."""

from __future__ import annotations

import json

from sanctuary import __version__
from sanctuary.library import archetype_index, specimen_card
from sanctuary.presets import PRESETS
from sanctuary.stats import fingerprint


def test_index_covers_library_deterministically() -> None:
    text = archetype_index()
    assert text == archetype_index()
    data = json.loads(text)
    assert data["generator"] == "sanctuary-g-code" and data["version"] == __version__
    assert [a["archetype"] for a in data["archetypes"]] == sorted(PRESETS)

    kelp = next(a for a in data["archetypes"] if a["archetype"] == "kelp-basin")
    assert kelp["systems"] == ["food", "water", "shelter", "hazard-patrol"]

    for entry in data["archetypes"]:
        assert set(entry) == {
            "archetype",
            "version",
            "description",
            "width",
            "height",
            "systems",
            "params",
            "theory",
            "reproduce",
        }
        assert entry["theory"]["water_gap_center"] > 0.0
        assert entry["theory"]["hazard_coverage_center"] > 0.0


def test_specimen_card_carries_provenance_and_fingerprint() -> None:
    data = json.loads(specimen_card(0, PRESETS["meadow"], 20))
    spec = data["specimen"]
    assert spec["generator"] == "sanctuary-g-code"
    assert spec["archetype"] == "meadow" and spec["archetype_version"] == 1
    assert spec["seed"] == 0 and spec["samples"] == 20

    fp = fingerprint(0, PRESETS["meadow"], 20)
    assert data["fingerprint"]["water_gap_food_median"] == fp.water_gap_food_median
    assert data["fingerprint"]["hazard_coverage_mean"] == fp.hazard_coverage_mean
