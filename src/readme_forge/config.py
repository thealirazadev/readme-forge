"""Config dataclass and resolution of model, sections, and color from flags/env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from readme_forge.api import DEFAULT_MODEL

DEFAULT_SECTIONS = [
    "overview",
    "features",
    "tech stack",
    "prerequisites",
    "installation",
    "usage",
    "project structure",
    "license",
]


@dataclass
class Config:
    target_path: Path
    output_path: Path
    overwrite: bool
    dry_run: bool
    model: str
    sections: list[str]
    quiet: bool
    verbose: bool
    color: bool


def resolve_model(model_flag: str | None) -> str:
    """Resolve the Claude model id: --model > README_FORGE_MODEL > built-in default."""
    return model_flag or os.environ.get("README_FORGE_MODEL") or DEFAULT_MODEL


def resolve_sections(sections_flag: str | None) -> list[str]:
    """Resolve the requested README sections from a comma-separated flag value."""
    if not sections_flag:
        return list(DEFAULT_SECTIONS)
    return [section.strip() for section in sections_flag.split(",") if section.strip()]


def resolve_color(isatty: bool) -> bool:
    """Resolve whether color output is enabled: NO_COLOR (any value) always wins."""
    if os.environ.get("NO_COLOR") is not None:
        return False
    return isatty
