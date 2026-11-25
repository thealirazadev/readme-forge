"""Language weighting by file extension and recognized manifest parsing."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import yaml

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


def _table(value: Any) -> dict:
    """Return value if it is a mapping, else an empty dict (manifests are user-controlled)."""
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str | None:
    """Return value if it is a string, else None."""
    return value if isinstance(value, str) else None


def _dependency_names(*tables: Any) -> list[str]:
    """Collect dependency names (the keys) from one or more dependency tables, in order."""
    names: list[str] = []
    for table in tables:
        for name in _table(table):
            if isinstance(name, str) and name not in names:
                names.append(name)
    return names[:MAX_DEPENDENCIES]


def _parse_package_json(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        notes.append(f"skipped malformed manifest: {path}")
        return None
    scripts = {k: v for k, v in _table(data.get("scripts")).items() if isinstance(v, str)}
    return Manifest(
        kind="package.json",
        path=path,
        name=_text(data.get("name")),
        description=_text(data.get("description")),
        version=_text(data.get("version")),
        scripts=scripts,
        dependencies=_dependency_names(data.get("dependencies"), data.get("devDependencies")),
    )


def _parse_pyproject_toml(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        notes.append(f"skipped malformed manifest: {path}")
        return None
    project = _table(data.get("project"))
    raw_deps = project.get("dependencies")
    deps = [d for d in raw_deps if isinstance(d, str)] if isinstance(raw_deps, list) else []
    scripts = {k: v for k, v in _table(project.get("scripts")).items() if isinstance(v, str)}
    return Manifest(
        kind="pyproject.toml",
        path=path,
        name=_text(project.get("name")),
        description=_text(project.get("description")),
        version=_text(project.get("version")),
        scripts=scripts,
        dependencies=deps[:MAX_DEPENDENCIES],
    )


def _parse_cargo_toml(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        notes.append(f"skipped malformed manifest: {path}")
        return None
    package = _table(data.get("package"))
    return Manifest(
        kind="Cargo.toml",
        path=path,
        name=_text(package.get("name")),
        description=_text(package.get("description")),
        version=_text(package.get("version")),
        dependencies=_dependency_names(
            data.get("dependencies"), data.get("dev-dependencies"), data.get("build-dependencies")
        ),
    )


def _parse_composer_json(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        notes.append(f"skipped malformed manifest: {path}")
        return None
    scripts: dict[str, str] = {}
    for key, value in _table(data.get("scripts")).items():
        if isinstance(value, str):
            scripts[key] = value
        elif isinstance(value, list) and value and all(isinstance(v, str) for v in value):
            # Composer runs a list of commands in order and stops at the first failure.
            scripts[key] = " && ".join(value)
    return Manifest(
        kind="composer.json",
        path=path,
        name=_text(data.get("name")),
        description=_text(data.get("description")),
        version=_text(data.get("version")),
        scripts=scripts,
        dependencies=_dependency_names(data.get("require"), data.get("require-dev")),
    )


def _parse_pubspec_yaml(path: str, content: str, notes: list[str]) -> Manifest | None:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        data = None
    if not isinstance(data, dict):
        notes.append(f"skipped malformed manifest: {path}")
        return None
    version = data.get("version")
    return Manifest(
        kind="pubspec.yaml",
        path=path,
        name=_text(data.get("name")),
        description=_text(data.get("description")),
        # An unquoted version such as 1.0 is loaded by YAML as a float.
        version=(
            str(version)
            if isinstance(version, (str, int, float)) and not isinstance(version, bool)
            else None
        ),
        dependencies=_dependency_names(data.get("dependencies"), data.get("dev_dependencies")),
    )


_GEM_LINE = re.compile(r"""^\s*gem\s*\(?\s*["']([^"']+)["']""")


def _parse_gemfile(path: str, content: str, notes: list[str]) -> Manifest | None:
    deps: list[str] = []
    for line in content.splitlines():
        match = _GEM_LINE.match(line)
        if match and match.group(1) not in deps:
            deps.append(match.group(1))
    return Manifest(kind="Gemfile", path=path, dependencies=deps[:MAX_DEPENDENCIES])


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
    "Cargo.toml": _parse_cargo_toml,
    "composer.json": _parse_composer_json,
    "pubspec.yaml": _parse_pubspec_yaml,
    "Gemfile": _parse_gemfile,
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
