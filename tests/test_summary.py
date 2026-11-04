from __future__ import annotations

from pathlib import Path

from readme_forge.detect import detect_languages, parse_manifests
from readme_forge.scanner import ScannedFile, scan_repo
from readme_forge.summary import MAX_SUMMARY_BYTES, _detect_has_ci, build_summary


def _summarize(root: Path):
    result = scan_repo(root)
    languages = detect_languages(result.files)
    manifests = parse_manifests(result.manifest_contents, result.notes)
    return build_summary(root, result.files, languages, manifests, result.notes)


def test_python_repo_summary(fixtures_dir: Path) -> None:
    summary = _summarize(fixtures_dir / "python_repo")
    assert summary.languages[0].name == "Python"
    assert any(m.kind == "pyproject.toml" for m in summary.manifests)
    assert summary.has_tests is True


def test_node_repo_summary(fixtures_dir: Path) -> None:
    summary = _summarize(fixtures_dir / "node_repo")
    assert summary.languages[0].name == "JavaScript"
    assert "build" in summary.scripts
    assert "test" in summary.scripts


def test_go_repo_summary(fixtures_dir: Path) -> None:
    summary = _summarize(fixtures_dir / "go_repo")
    assert summary.languages[0].name == "Go"
    assert any(m.kind == "go.mod" for m in summary.manifests)


def test_empty_repo_summary_is_clearly_empty(tmp_path: Path) -> None:
    summary = _summarize(tmp_path)
    assert summary.file_count == 0
    assert summary.languages == []
    assert summary.manifests == []


def test_summary_is_deterministic(fixtures_dir: Path) -> None:
    first = _summarize(fixtures_dir / "mixed_repo")
    second = _summarize(fixtures_dir / "mixed_repo")
    assert first.to_dict() == second.to_dict()


def test_summary_size_cap_enforced(tmp_path: Path) -> None:
    result = scan_repo(tmp_path)
    huge_notes = [f"note number {i} with some extra padding text" for i in range(2000)]
    summary = build_summary(tmp_path, result.files, [], [], huge_notes)
    assert len(summary.to_json().encode("utf-8")) <= MAX_SUMMARY_BYTES


def test_has_ci_detected_from_files_under_ci_directories(tmp_path: Path) -> None:
    circleci = [ScannedFile(relative_path=".circleci/config.yml", extension=".yml", size=10)]
    workflows = [ScannedFile(relative_path=".github/workflows/ci.yml", extension=".yml", size=10)]
    gitlab = [ScannedFile(relative_path=".gitlab-ci.yml", extension=".yml", size=10)]
    unrelated = [ScannedFile(relative_path="src/.circleci_notes.txt", extension=".txt", size=10)]
    assert _detect_has_ci(tmp_path, circleci) is True
    assert _detect_has_ci(tmp_path, workflows) is True
    assert _detect_has_ci(tmp_path, gitlab) is True
    assert _detect_has_ci(tmp_path, unrelated) is False
