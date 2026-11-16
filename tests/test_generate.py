"""Generation: counts, spatial invariants, determinism."""

from __future__ import annotations

from math import hypot, isfinite

from sanctuary.generate import generate
from sanctuary.presets import PRESETS
from sanctuary.world import Hazard


def _check(preset_name: str, seed: int) -> None:
    preset = PRESETS[preset_name]
    w = generate(seed, preset)
    assert w.preset == preset_name
    assert w.preset_version == preset.version
    assert w.seed == seed
    assert w.name == f"{preset_name}_s{seed}"

    assert len(w.food) == preset.food_count
    assert len(w.water) == preset.water_count
    assert len(w.shelters) == preset.shelter_count
    assert len(w.hazards) <= preset.permanent_hazards + preset.patrols

    # everything inside the world, with margin
    for e in (*w.food, *w.water, *w.shelters, *w.hazards):
        assert 0.0 < e.x < preset.width
        assert 0.0 < e.y < preset.height

    # food patches keep their minimum pairwise gap (up to relaxation halving)
    for i, a in enumerate(w.food):
        for b in w.food[i + 1 :]:
            assert hypot(a.x - b.x, a.y - b.y) >= preset.min_food_gap / 2

    # the organism starts at home
    assert w.start == (w.shelters[0].x, w.shelters[0].y)

    # permanent hazards never reach the shelter, patrols are finite and daily
    for hz in w.hazards:
        if isinstance(hz, Hazard) and hz.scheduled:
            assert isfinite(hz.start) and isfinite(hz.end) and isfinite(hz.every)
            assert hz.end > hz.start
        else:
            assert hypot(hz.x - w.shelters[0].x, hz.y - w.shelters[0].y) > hz.radius + w.shelters[0].radius


def test_all_presets_multiple_seeds() -> None:
    for name in PRESETS:
        for seed in (0, 1, 7, 42, 20261116):
            _check(name, seed)


def test_determinism() -> None:
    assert generate(3, PRESETS["meadow"]) == generate(3, PRESETS["meadow"])


def test_seed_changes_the_world() -> None:
    assert generate(1, PRESETS["meadow"]) != generate(2, PRESETS["meadow"])


def test_preset_changes_the_world() -> None:
    assert generate(1, PRESETS["meadow"]) != generate(1, PRESETS["dryland"])


def test_patrols_land_on_food_patches() -> None:
    w = generate(1, PRESETS["meadow"])
    patrols = [h for h in w.hazards if h.scheduled]
    assert len(patrols) == PRESETS["meadow"].patrols
    for h in patrols:
        assert any(hypot(h.x - f.x, h.y - f.y) < 1e-9 for f in w.food)
