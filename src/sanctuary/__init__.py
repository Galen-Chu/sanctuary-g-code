"""Sanctuary G-Code: deterministic procedural worlds for embodied minds.

``sanctuary.generate(seed, preset)`` builds a World from nothing but a seed
and a preset; ``sanctuary.toml_out`` renders it as a Unbodysoma scenario.
Pipeline lineage: Noniv/abyssal-garden (MIT) — see docs/DESIGN.md.
"""

from __future__ import annotations

from .generate import generate
from .presets import PRESETS, Preset
from .world import FoodPatch, Hazard, Shelter, WaterSource, World

__version__ = "0.1.0"

__all__ = [
    "PRESETS",
    "FoodPatch",
    "Hazard",
    "Preset",
    "Shelter",
    "WaterSource",
    "World",
    "generate",
    "__version__",
]
