"""Population mode: N worlds from one master seed plus a group manifest.

The M1 ``N organisms x M worlds`` experiments (BACKLOG section 2) need the
world side as one addressable unit: derive N world seeds from a master seed,
emit one scenario TOML per world, and one manifest carrying the group-level
provenance — generator version, preset@version, master seed, and each file's
SHA-256 — so a run record can cite a whole population with a single file.

Derivation contract (as stable as the system ids in DESIGN.md section 2):
world ``i`` of a population from master seed ``s`` is exactly
``generate(s + i, preset)``. Every world in a population is reproducible
with the plain single-world CLI, and populations need no RNG of their own.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from . import __version__
from .generate import generate
from .presets import Preset
from .toml_out import _f
from .world import World

MANIFEST_NAME = "population.toml"


def generate_population(seed: int, preset: Preset, count: int) -> tuple[World, ...]:
    """Worlds ``0..count-1`` as ``generate(seed + i, preset)`` — pure, ordered by seed."""
    if count < 1:
        raise ValueError(f"population count must be >= 1, got {count}")
    return tuple(generate(seed + i, preset) for i in range(count))


def world_filename(world: World) -> str:
    """Scenario file name inside a population directory: ``<world name>.toml``."""
    return f"{world.name}.toml"


def population_manifest(
    worlds: Sequence[World],
    texts: Sequence[str],
    *,
    duration_h: float = 72.0,
    organism_seed: int | None = None,
) -> str:
    """Render the manifest for one population run.

    ``texts[i]`` must be the ``scenario_toml`` output of ``worlds[i]``; each
    entry pins its file's SHA-256, so the population verifies as a unit.
    Like every artifact here the manifest is a pure function of its inputs —
    no timestamps, so a rerun is byte-identical.
    """
    if len(worlds) != len(texts):
        raise ValueError(f"worlds ({len(worlds)}) and scenario texts ({len(texts)}) must pair up")
    head = worlds[0]
    lines: list[str] = [
        "# Sanctuary population manifest — the group provenance of one --count run.",
        f"# Reproduce: sanctuary --seed {head.seed} --preset {head.preset} "
        f"--count {len(worlds)} --out <this directory>",
        "",
        "[population]",
        'generator = "sanctuary-g-code"',
        f'version = "{__version__}"',
        f'preset = "{head.preset}@{head.preset_version}"',
        f"seed = {head.seed}",
        f"count = {len(worlds)}",
        f"duration_h = {_f(duration_h)}",
    ]
    if organism_seed is not None:
        lines.append(f"organism_seed = {organism_seed}")
    for world, text in zip(worlds, texts, strict=True):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        lines += [
            "",
            "[[worlds]]",
            f'name = "{world.name}"',
            f'file = "{world_filename(world)}"',
            f"seed = {world.seed}",
            f'sha256 = "{digest}"',
        ]
    lines.append("")
    return "\n".join(lines)
