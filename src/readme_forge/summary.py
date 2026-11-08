"""Build a bounded, deterministic RepoSummary from scan and detection results."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from readme_forge.detect import LanguageStat, Manifest
from readme_forge.scanner import ScannedFile

MAX_TOP_LEVEL = 40
MAX_ENTRY_POINTS = 20
MAX_SCRIPTS = 30
MAX_STRING_LEN = 500
MAX_SUMMARY_BYTES = 20_000

ENTRY_POINT_NAMES = {
    "main.py",
    "__main__.py",
    "app.py",
    "manage.py",
    "index.js",
    "index.ts",
    "server.js",
    "main.go",
}

CI_MARKER_PATHS = (".github/workflows", ".gitlab-ci.yml", ".circleci")

LICENSE_FILENAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md")


@dataclass
class RepoSummary:
    root_name: str
    file_count: int
    languages: list[LanguageStat] = field(default_factory=list)
    manifests: list[Manifest] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)
    entry_points: list[str] = field(default_factory=list)
    top_level: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_ci: bool = False
    license_hint: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _truncate(value: str) -> str:
    if len(value) <= MAX_STRING_LEN:
        return value
    return value[: MAX_STRING_LEN - 1] + "…"


def _detect_entry_points(files: list[ScannedFile]) -> list[str]:
    found = {f.relative_path for f in files if Path(f.relative_path).name in ENTRY_POINT_NAMES}
    return sorted(found)[:MAX_ENTRY_POINTS]


def _detect_top_level(files: list[ScannedFile]) -> list[str]:
    """Top-level names taken from scanned files only.

    Listing the directory directly would leak gitignored paths (node_modules, build output),
    secret files, and skipped binaries into the prompt; the scanner already filtered those.
    """
    entries = sorted({Path(f.relative_path).parts[0] for f in files if f.relative_path})
    return entries[:MAX_TOP_LEVEL]


def _detect_has_tests(files: list[ScannedFile]) -> bool:
    for f in files:
        p = Path(f.relative_path)
        if "tests" in p.parts or "test" in p.parts:
            return True
        if p.stem.startswith("test_") or p.stem.endswith("_test"):
            return True
    return False


def _detect_has_ci(root: Path, files: list[ScannedFile]) -> bool:
    if (root / ".github" / "workflows").is_dir():
        return True
    present = {f.relative_path for f in files}
    return any(marker in present for marker in CI_MARKER_PATHS)


def _detect_license_hint(root: Path) -> str | None:
    for filename in LICENSE_FILENAMES:
        if (root / filename).is_file():
            return filename
    return None


def _merge_scripts(manifests: list[Manifest]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for manifest in manifests:
        for key, value in manifest.scripts.items():
            if key not in merged:
                merged[key] = _truncate(value)
    return dict(list(merged.items())[:MAX_SCRIPTS])


def build_summary(
    root: Path,
    files: list[ScannedFile],
    languages: list[LanguageStat],
    manifests: list[Manifest],
    notes: list[str],
) -> RepoSummary:
    """Assemble a deterministic, size-bounded RepoSummary from scan results."""
    summary = RepoSummary(
        root_name=root.resolve().name or str(root),
        file_count=len(files),
        languages=languages,
        manifests=manifests,
        scripts=_merge_scripts(manifests),
        entry_points=_detect_entry_points(files),
        top_level=_detect_top_level(files),
        has_tests=_detect_has_tests(files),
        has_ci=_detect_has_ci(root, files),
        license_hint=_detect_license_hint(root),
        notes=list(notes),
    )
    _enforce_size_cap(summary)
    return summary


def _enforce_size_cap(summary: RepoSummary) -> None:
    """Trim least-essential fields until the serialized summary fits MAX_SUMMARY_BYTES."""
    while len(summary.to_json().encode("utf-8")) > MAX_SUMMARY_BYTES:
        if summary.notes:
            summary.notes.pop()
        elif summary.top_level:
            summary.top_level.pop()
        elif summary.entry_points:
            summary.entry_points.pop()
        elif summary.scripts:
            summary.scripts.pop(next(iter(summary.scripts)))
        elif len(summary.manifests) > 1:
            summary.manifests.pop()
        elif summary.languages:
            summary.languages.pop()
        else:
            break
