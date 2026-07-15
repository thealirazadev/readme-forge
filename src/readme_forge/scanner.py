"""Directory walk with .gitignore-aware ignoring and secret/large-file skipping."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path

import pathspec

# Files above this size are never read; this also covers large binaries.
MAX_FILE_SIZE = 500_000

BUILTIN_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "ENV",
    "dist",
    "build",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".tox",
    ".idea",
    ".vscode",
}

SECRET_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa",
    "*.p12",
    "credentials",
    "secrets.*",
)

RECOGNIZED_MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "composer.json",
    "pubspec.yaml",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "build.gradle",
    "pom.xml",
}


@dataclass
class ScannedFile:
    relative_path: str
    extension: str
    size: int


@dataclass
class ScanResult:
    root: Path
    files: list[ScannedFile] = field(default_factory=list)
    manifest_contents: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _is_secret(filename: str) -> bool:
    return any(fnmatch.fnmatch(filename, pattern) for pattern in SECRET_PATTERNS)


def _load_gitignore_spec(root: Path) -> pathspec.PathSpec | None:
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return None
    try:
        lines = gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def scan_repo(root: Path) -> ScanResult:
    """Walk root, applying ignore/secret/size rules, collecting file metadata.

    Only the contents of recognized manifest files are read; every other file
    body is skipped. Unreadable files are noted and skipped, never fatal.
    """
    result = ScanResult(root=root)
    spec = _load_gitignore_spec(root)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in BUILTIN_IGNORE_DIRS)
        rel_dir = Path(dirpath).relative_to(root)

        if spec is not None:
            dirnames[:] = [
                d for d in dirnames if not spec.match_file(f"{(rel_dir / d).as_posix()}/")
            ]

        for filename in sorted(filenames):
            rel_path = rel_dir / filename if str(rel_dir) != "." else Path(filename)
            rel_str = rel_path.as_posix()

            if spec is not None and spec.match_file(rel_str):
                continue

            if _is_secret(filename):
                result.notes.append(f"skipped secret file: {rel_str}")
                continue

            full_path = root / rel_path
            try:
                size = full_path.stat().st_size
            except OSError:
                result.notes.append(f"skipped unreadable file: {rel_str}")
                continue

            if size > MAX_FILE_SIZE:
                result.notes.append(f"skipped large file ({size} bytes): {rel_str}")
                continue

            result.files.append(
                ScannedFile(relative_path=rel_str, extension=full_path.suffix, size=size)
            )

            if filename in RECOGNIZED_MANIFESTS:
                try:
                    result.manifest_contents[rel_str] = full_path.read_text(
                        encoding="utf-8", errors="replace"
                    )
                except OSError:
                    result.notes.append(f"skipped unreadable manifest: {rel_str}")

    return result
