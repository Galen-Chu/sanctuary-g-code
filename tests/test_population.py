"""Population mode: derivation identity, manifest contract, CLI directory mode."""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

import pytest

from sanctuary import __version__
from sanctuary.__main__ import main
from sanctuary.generate import generate
from sanctuary.population import MANIFEST_NAME, generate_population, population_manifest, world_filename
from sanctuary.presets import PRESETS
from sanctuary.toml_out import scenario_toml


def test_derivation_identity() -> None:
    """World i of a population is exactly the standalone generate(seed + i)."""
    pop = generate_population(10, PRESETS["meadow"], 5)
    assert [w.seed for w in pop] == [10, 11, 12, 13, 14]
    for i, world in enumerate(pop):
        assert world == generate(10 + i, PRESETS["meadow"])


def test_count_validation() -> None:
    with pytest.raises(ValueError):
        generate_population(1, PRESETS["meadow"], 0)


def test_manifest_roundtrip_and_hashes() -> None:
    worlds = generate_population(1, PRESETS["meadow"], 3)
    texts = [scenario_toml(w) for w in worlds]
    data = tomllib.loads(population_manifest(worlds, texts))

    assert set(data) == {"population", "worlds"}
    pop = data["population"]
    assert set(pop) == {"generator", "version", "preset", "seed", "count", "duration_h"}
    assert pop["generator"] == "sanctuary-g-code"
    assert pop["version"] == __version__
    assert pop["preset"] == "meadow@1"
    assert pop["seed"] == 1 and pop["count"] == 3

    assert len(data["worlds"]) == 3
    for world, text, entry in zip(worlds, texts, data["worlds"], strict=True):
        assert set(entry) == {"name", "file", "seed", "sha256"}
        assert entry["name"] == world.name
        assert entry["file"] == world_filename(world)
        assert entry["seed"] == world.seed
        assert entry["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()

    # World 0 of this population is the golden world: the manifest's hash
    # ties it to the pinned golden bytes.
    golden = Path(__file__).parent / "golden" / "meadow_seed1.toml"
    assert data["worlds"][0]["sha256"] == hashlib.sha256(golden.read_bytes()).hexdigest()


def test_manifest_records_overrides() -> None:
    worlds = generate_population(5, PRESETS["meadow"], 2)
    texts = [scenario_toml(w, duration_h=48.0, organism_seed=99) for w in worlds]
    pop = tomllib.loads(population_manifest(worlds, texts, duration_h=48.0, organism_seed=99))["population"]
    assert pop["duration_h"] == 48.0
    assert pop["organism_seed"] == 99


def test_manifest_deterministic() -> None:
    worlds = generate_population(7, PRESETS["dryland"], 2)
    texts = [scenario_toml(w) for w in worlds]
    assert population_manifest(worlds, texts) == population_manifest(worlds, texts)


def test_golden_manifest() -> None:
    """Byte-pinned manifest: derivation, emission order, and all three hashes."""
    golden = Path(__file__).parent / "golden" / "population_meadow_seed1_count3.toml"
    worlds = generate_population(1, PRESETS["meadow"], 3)
    texts = [scenario_toml(w) for w in worlds]
    assert population_manifest(worlds, texts).encode("utf-8") == golden.read_bytes()


def test_cli_population_writes_directory(tmp_path: Path) -> None:
    out = tmp_path / "pops" / "meadow_x3"
    assert main(["--seed", "100", "--preset", "meadow", "--count", "3", "--out", str(out)]) == 0

    assert sorted(p.name for p in out.iterdir()) == [
        "meadow_s100.toml",
        "meadow_s101.toml",
        "meadow_s102.toml",
        MANIFEST_NAME,
    ]
    manifest = tomllib.loads((out / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["population"]["count"] == 3
    for entry in manifest["worlds"]:
        blob = (out / entry["file"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == entry["sha256"]


def test_cli_population_rejects_stdout() -> None:
    with pytest.raises(SystemExit):
        main(["--seed", "1", "--count", "3", "--out", "-"])
