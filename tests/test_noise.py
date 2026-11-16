"""Noise: bounds, lattice determinism, smoothstep endpoints."""

from __future__ import annotations

from sanctuary.noise import _ihash2, clamp, fbm2, mix, ss, vnoise2


def test_vnoise_bounds_including_negatives() -> None:
    for x in range(-30, 30, 3):
        for y in range(-30, 30, 3):
            v = vnoise2(x * 0.37, y * 0.61)
            assert 0.0 <= v < 1.0


def test_fbm_bounds() -> None:
    for i in range(200):
        x = (i * 13.7) % 40 - 20
        y = (i * 7.3) % 40 - 20
        for octaves in (1, 2, 3, 4, 6):
            v = fbm2(x, y, octaves)
            assert 0.0 <= v < 1.0


def test_lattice_hash_is_deterministic() -> None:
    assert _ihash2(3, 4) == _ihash2(3, 4)
    assert _ihash2(3, 4) != _ihash2(4, 3)
    assert 0.0 <= _ihash2(-5, 17) < 1.0


def test_vnoise_matches_lattice_at_integer_points() -> None:
    assert vnoise2(2.0, 3.0) == _ihash2(2, 3)


def test_smoothstep_endpoints() -> None:
    assert ss(0.0, 1.0, -1.0) == 0.0
    assert ss(0.0, 1.0, 2.0) == 1.0
    assert 0.0 < ss(0.0, 1.0, 0.5) < 1.0


def test_scalar_helpers() -> None:
    assert clamp(5.0, 0.0, 1.0) == 1.0
    assert clamp(-5.0, 0.0, 1.0) == 0.0
    assert mix(0.0, 10.0, 0.25) == 2.5
