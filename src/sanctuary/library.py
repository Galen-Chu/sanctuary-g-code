"""The world library: archetype index and specimen cards as deterministic JSON.

The JSON artifacts are the reference adapter for library data (DESIGN §4):
the index describes every archetype (composition, parameters, theory
centres), the specimen card pins one archetype's cross-seed fingerprint.
Worlds themselves are never stored — a world is a pure function of
(seed, archetype@version), so an index card is the whole archive entry;
regenerate on demand.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from . import __version__
from .presets import PRESETS, Preset
from .stats import expected_hazard_coverage, fingerprint, poisson_median_nearest
from .systems import validate_composition


def _theory(preset: Preset) -> dict[str, float]:
    return {
        "water_gap_center": poisson_median_nearest((preset.width - 4) * (preset.height - 4), preset.water_count),
        "hazard_coverage_center": expected_hazard_coverage(preset),
    }


def _archetype_entry(preset: Preset) -> dict[str, object]:
    return {
        "archetype": preset.name,
        "version": preset.version,
        "description": preset.description,
        "width": preset.width,
        "height": preset.height,
        "systems": list(validate_composition(preset.systems)),
        "params": {
            "food_count": preset.food_count,
            "water_count": preset.water_count,
            "shelter_count": preset.shelter_count,
            "permanent_hazards": preset.permanent_hazards,
            "patrols": preset.patrols,
            "patrol_strategy": preset.patrol_strategy,
            "fertility_scale": preset.fertility_scale,
            "regrow_per_hour": preset.regrow_per_hour,
            "min_food_gap": preset.min_food_gap,
            "min_water_gap": preset.min_water_gap,
            "hazard_clearance": preset.hazard_clearance,
        },
        "theory": _theory(preset),
        "reproduce": f"sanctuary --seed <seed> --preset {preset.name}",
    }


def archetype_index() -> str:
    """JSON index of the whole archetype library (deterministic bytes)."""
    entries = [_archetype_entry(preset) for _, preset in sorted(PRESETS.items())]
    payload = {"generator": "sanctuary-g-code", "version": __version__, "archetypes": entries}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def specimen_card(seed: int, preset: Preset, count: int = 100) -> str:
    """JSON specimen card: provenance plus the archetype's cross-seed fingerprint."""
    fp = fingerprint(seed, preset, count)
    card = {
        "specimen": {
            "generator": "sanctuary-g-code",
            "generator_version": __version__,
            "archetype": preset.name,
            "archetype_version": preset.version,
            "seed": seed,
            "samples": count,
        },
        "fingerprint": asdict(fp),
    }
    return json.dumps(card, ensure_ascii=False, sort_keys=True)
