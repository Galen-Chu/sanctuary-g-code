"""Statistical acceptance: bands calibrated from generation-rule theory.

Centres come from executable theory (``poisson_median_nearest``,
``expected_hazard_coverage``); the factors are documented in ``stats.py``
and DESIGN.md section 5. CI checks 50 seeds per preset — a median has
ample power against gross-degeneracy bands; the CLI default is 100.
"""

from __future__ import annotations

import math

import pytest

from sanctuary.generate import generate
from sanctuary.presets import PRESETS
from sanctuary.stats import (
    COVERAGE_BAND_FACTOR,
    SHELTER_FOOD_BAND,
    WATER_BAND_FACTOR,
    Fingerprint,
    expected_hazard_coverage,
    fingerprint,
    format_fingerprint,
    hazard_coverage,
    patrol_clock_hours,
    poisson_median_nearest,
)
from sanctuary.world import Hazard, World

SEED0 = 0
N = 50

_cache: dict[str, Fingerprint] = {}


def fp(name: str) -> Fingerprint:
    """One fingerprint per preset for the whole module (deterministic)."""
    if name not in _cache:
        _cache[name] = fingerprint(SEED0, PRESETS[name], N)
    return _cache[name]


def water_center(name: str) -> float:
    p = PRESETS[name]
    return poisson_median_nearest((p.width - 4) * (p.height - 4), p.water_count)


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_water_gap_median_in_band(name: str) -> None:
    """Median food-to-nearest-water distance sits within the Poisson band."""
    center = water_center(name)
    lo, hi = WATER_BAND_FACTOR
    assert lo * center <= fp(name).water_gap_food_median <= hi * center


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_shelter_water_median_in_band(name: str) -> None:
    """Shelter-to-nearest-water median sits within the same Poisson band."""
    center = water_center(name)
    lo, hi = WATER_BAND_FACTOR
    assert lo * center <= fp(name).shelter_water_median <= hi * center


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_shelter_food_median_in_band(name: str) -> None:
    """Shelter-to-nearest-food median stays in the offset range plus slack."""
    lo, hi = SHELTER_FOOD_BAND
    assert lo <= fp(name).shelter_food_median <= hi


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_hazard_coverage_in_band(name: str) -> None:
    """Mean hazard coverage sits within the independent-disk band."""
    center = expected_hazard_coverage(PRESETS[name])
    lo, hi = COVERAGE_BAND_FACTOR
    assert lo * center <= fp(name).hazard_coverage_mean <= hi * center


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_patrol_hours_are_cyclic_slots(name: str) -> None:
    """Patrols fire in slots {11,14,17,20} cyclically, each with +-0.5h jitter.

    Structural, not statistical: slot assignment is by draw index, so meadow
    (2 patrols) always covers 11h and 14h -- a rigidity the patrol strategy
    library (BACKLOG section 1) exists to break.
    """
    slots = (11.0, 14.0, 17.0, 20.0)
    for seed in range(SEED0, SEED0 + 10):
        hours = patrol_clock_hours(generate(seed, PRESETS[name]))
        assert len(hours) == PRESETS[name].patrols
        for j, hour in enumerate(hours):
            assert abs(hour - slots[j % len(slots)]) <= 0.5 + 1e-9


def test_hazard_coverage_single_disk() -> None:
    """The grid estimator recovers pi*r^2/A for one centred disk."""
    world = World(
        name="t",
        preset="t",
        preset_version=1,
        seed=0,
        width=20.0,
        height=20.0,
        start=(10.0, 10.0),
        hazards=(Hazard(10.0, 10.0, radius=5.0, strength=0.9),),
    )
    assert abs(hazard_coverage(world) - math.pi * 25.0 / 400.0) < 0.01


def test_fingerprint_deterministic() -> None:
    assert fingerprint(3, PRESETS["meadow"], 10) == fingerprint(3, PRESETS["meadow"], 10)


def test_format_fingerprint_mentions_band() -> None:
    text = format_fingerprint(fingerprint(1, PRESETS["meadow"], 5), PRESETS["meadow"])
    assert "band" in text and "meadow" in text
