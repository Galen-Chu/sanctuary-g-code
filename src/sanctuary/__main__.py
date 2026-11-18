"""CLI: sanctuary --seed 1 --preset meadow --out world.toml [--count N]"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from .generate import generate
from .population import MANIFEST_NAME, generate_population, population_manifest, world_filename
from .presets import PRESETS
from .toml_out import scenario_toml
from .world import World


def _write(path: Path, text: str) -> None:
    # newline="\n" keeps the bytes identical on every platform (golden tests depend on it)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _report(world: World, dest: str, text: str) -> None:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(
        f"{world.name}: {len(world.food)} food, {len(world.water)} water, "
        f"{len(world.shelters)} shelter, {len(world.hazards)} hazards -> "
        f"{dest}  sha256:{digest[:16]}",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sanctuary",
        description="Deterministic procedural world generator (Unbodysoma-compatible TOML output)",
    )
    parser.add_argument("--seed", type=int, default=0, help="base seed of the world (default: 0)")
    parser.add_argument("--preset", default="meadow", choices=sorted(PRESETS), help="world preset (default: meadow)")
    parser.add_argument("--out", default="-", help="output TOML path, or - for stdout (default: -)")
    parser.add_argument("--hours", type=float, default=72.0, help="scenario duration_h (default: 72)")
    parser.add_argument(
        "--organism-seed",
        type=int,
        default=None,
        help="override the scenario seed the organism's stochasticity uses (default: same as --seed)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="population mode: N worlds with seeds seed..seed+N-1 written to --out DIR "
        "plus a population.toml manifest (default: 1, single world)",
    )
    parser.add_argument("--list-presets", action="store_true", help="list presets and exit")
    args = parser.parse_args(argv)

    if args.list_presets:
        for name in sorted(PRESETS):
            p = PRESETS[name]
            print(
                f"{name:12} {p.width:g}x{p.height:g}  food={p.food_count} water={p.water_count} "
                f"hazards={p.permanent_hazards}+{p.patrols}p  {p.description}"
            )
        return 0

    if args.count < 1:
        parser.error("--count must be >= 1")

    preset = PRESETS[args.preset]

    if args.count == 1:
        world = generate(args.seed, preset)
        text = scenario_toml(world, duration_h=args.hours, organism_seed=args.organism_seed)
        if args.out == "-":
            sys.stdout.write(text)
            _report(world, "stdout", text)
        else:
            _write(Path(args.out), text)
            _report(world, args.out, text)
        return 0

    # Population mode: --out is a directory holding N scenarios plus the manifest.
    if args.out == "-":
        parser.error("--count > 1 writes a directory of files: pass --out DIR")
    outdir = Path(args.out)
    if outdir.exists() and not outdir.is_dir():
        parser.error(f"--out exists and is not a directory: {outdir}")
    worlds = generate_population(args.seed, preset, args.count)
    texts = [scenario_toml(w, duration_h=args.hours, organism_seed=args.organism_seed) for w in worlds]
    outdir.mkdir(parents=True, exist_ok=True)
    for world, text in zip(worlds, texts, strict=True):
        _write(outdir / world_filename(world), text)
        _report(world, world_filename(world), text)
    manifest = population_manifest(worlds, texts, duration_h=args.hours, organism_seed=args.organism_seed)
    _write(outdir / MANIFEST_NAME, manifest)
    print(
        f"population {preset.name}@{preset.version}: {len(worlds)} worlds, "
        f"seeds {worlds[0].seed}..{worlds[-1].seed} -> {outdir / MANIFEST_NAME}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
