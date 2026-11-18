"""Patrol strategy library: distinguishable behaviour, stream isolation, validation."""

from __future__ import annotations

import dataclasses

import pytest

from sanctuary.generate import generate
from sanctuary.presets import PRESETS
from sanctuary.stats import patrol_clock_hours
from sanctuary.strategies import STRATEGIES, validate_strategy

_SLOTS = (11.0, 14.0, 17.0, 20.0)


def variant(strategy: str):
    return dataclasses.replace(PRESETS["meadow"], name=f"t-{strategy}", patrol_strategy=strategy)


def test_fixed_keeps_phase1_slots() -> None:
    for seed in range(10):
        hours = patrol_clock_hours(generate(seed, variant("fixed")))
        assert len(hours) == 2
        for j, hour in enumerate(hours):
            assert abs(hour - _SLOTS[j]) <= 0.5 + 1e-9


def test_strategy_changes_only_patrol_stream() -> None:
    """Per-system streams: a strategy swap leaves every other entity identical."""
    worlds = {s: generate(7, variant(s)) for s in STRATEGIES}
    base = worlds["fixed"]
    for strategy, world in worlds.items():
        assert world.food == base.food, strategy
        assert world.water == base.water, strategy
        assert world.shelters == base.shelters, strategy
    assert len({w.hazards for w in worlds.values()}) == len(STRATEGIES)


def test_sweep_spreads_over_the_whole_day() -> None:
    hours = [h for seed in range(10) for h in patrol_clock_hours(generate(seed, variant("sweep")))]
    assert all(8.0 <= h < 32.0 for h in hours)
    assert max(hours) - min(hours) > 15.0  # uniform over 24 h, unlike any other strategy


def test_circadian_holds_a_strict_period() -> None:
    for seed in range(10):
        hours = patrol_clock_hours(generate(seed, variant("circadian")))
        assert all(8.0 <= h < 20.5 for h in hours)
        for a, b in zip(hours, hours[1:], strict=False):
            assert abs((b - a) - 6.0) <= 0.5 + 1e-9


def test_regional_concentrates_on_one_anchor() -> None:
    for seed in range(10):
        world = generate(seed, variant("regional"))
        patrol = [h for h in world.hazards if h.scheduled]
        assert len({(h.x, h.y) for h in patrol}) == 1
        for j, hour in enumerate(patrol_clock_hours(world)):
            assert abs(hour - _SLOTS[j]) <= 0.5 + 1e-9


def test_strategies_are_pairwise_separated_in_time() -> None:
    """Median patrol gap: fixed ~3 h, circadian exactly 6 h — disjoint bands."""
    gaps = {}
    for strategy in ("fixed", "circadian"):
        per_world = []
        for seed in range(10):
            hours = sorted(patrol_clock_hours(generate(seed, variant(strategy))))
            per_world.append(hours[1] - hours[0])
        gaps[strategy] = sorted(per_world)[len(per_world) // 2]
    assert gaps["fixed"] < 4.5 < gaps["circadian"]


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown patrol strategy"):
        validate_strategy("ambush")
    with pytest.raises(ValueError, match="unknown patrol strategy"):
        generate(1, variant("ambush"))


def test_meadow_variants_share_meadow_resources() -> None:
    """The library variants differ from meadow only in predator behaviour."""
    meadow = generate(3, PRESETS["meadow"])
    for name in ("meadow-roam", "meadow-tide", "meadow-focal"):
        world = generate(3, PRESETS[name])
        assert world.food == meadow.food
        assert world.water == meadow.water
        assert world.shelters == meadow.shelters
        assert world.hazards != meadow.hazards
