"""CLI: sanctuary --seed 1 --preset meadow --out world.toml"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from .generate import generate
from .presets import PRESETS
from .toml_out import scenario_toml


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

    world = generate(args.seed, PRESETS[args.preset])
    text = scenario_toml(world, duration_h=args.hours, organism_seed=args.organism_seed)
    if args.out == "-":
        sys.stdout.write(text)
    else:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" keeps the bytes identical on every platform (golden tests depend on it)
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(
        f"{world.name}: {len(world.food)} food, {len(world.water)} water, "
        f"{len(world.shelters)} shelter, {len(world.hazards)} hazards -> "
        f"{'stdout' if args.out == '-' else args.out}  sha256:{digest[:16]}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
