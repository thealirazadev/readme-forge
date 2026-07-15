"""Language weighting by file extension and recognized manifest parsing."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from readme_forge.scanner import ScannedFile

MAX_LANGUAGES = 8
MAX_DEPENDENCIES = 30

EXTENSION_LANGUAGES = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".dart": "Dart",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
}


@dataclass
class LanguageStat:
    name: str
    file_count: int
    weight: float


def detect_languages(files: list[ScannedFile]) -> list[LanguageStat]:
    """Weight languages by their share of recognized code files."""
    counts: dict[str, int] = {}
    for scanned in files:
        language = EXTENSION_LANGUAGES.get(scanned.extension.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return []

    stats = [
        LanguageStat(name=name, file_count=count, weight=round(count / total, 4))
        for name, count in counts.items()
    ]
    stats.sort(key=lambda s: (-s.weight, s.name))
    return stats[:MAX_LANGUAGES]


@dataclass
class Manifest:
    kind: str
    path: str
    name: str | None = None
    description: str | None = None
    version: str | None = None
    scripts: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


def _parse_package_json(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        notes.append(f"skipped malformed manifest: {path}")
        return None
    deps = list(data.get("dependencies", {}) or {}) + list(data.get("devDependencies", {}) or {})
    scripts = {k: v for k, v in (data.get("scripts") or {}).items() if isinstance(v, str)}
    return Manifest(
        kind="package.json",
        path=path,
        name=data.get("name"),
        description=data.get("description"),
        version=data.get("version"),
        scripts=scripts,
        dependencies=deps[:MAX_DEPENDENCIES],
    )


def _parse_pyproject_toml(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        notes.append(f"skipped malformed manifest: {path}")
        return None
    project = data.get("project") or {}
    deps = list(project.get("dependencies") or [])
    scripts = dict(project.get("scripts") or {})
    return Manifest(
        kind="pyproject.toml",
        path=path,
        name=project.get("name"),
        description=project.get("description"),
        version=project.get("version"),
        scripts=scripts,
        dependencies=deps[:MAX_DEPENDENCIES],
    )


def _parse_go_mod(path: str, content: str, notes: list[str]) -> Manifest | None:
    name = None
    deps: list[str] = []
    in_require_block = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("module "):
            name = stripped[len("module ") :].strip()
        elif stripped.startswith("require ("):
            in_require_block = True
        elif in_require_block and stripped == ")":
            in_require_block = False
        elif in_require_block and stripped:
            deps.append(stripped.split()[0])
        elif stripped.startswith("require ") and not in_require_block:
            parts = stripped[len("require ") :].split()
            if parts:
                deps.append(parts[0])

    if name is None:
        notes.append(f"skipped malformed manifest: {path}")
        return None
    return Manifest(kind="go.mod", path=path, name=name, dependencies=deps[:MAX_DEPENDENCIES])


_PARSERS = {
    "package.json": _parse_package_json,
    "pyproject.toml": _parse_pyproject_toml,
    "go.mod": _parse_go_mod,
}


def parse_manifests(manifest_contents: dict[str, str], notes: list[str]) -> list[Manifest]:
    """Parse recognized manifest contents into Manifest objects; malformed ones are skipped."""
    manifests: list[Manifest] = []
    for path, content in manifest_contents.items():
        filename = path.rsplit("/", 1)[-1]
        parser = _PARSERS.get(filename)
        if parser is None:
            continue
        manifest = parser(path, content, notes)
        if manifest is not None:
            manifests.append(manifest)
    manifests.sort(key=lambda m: m.path)
    return manifests
