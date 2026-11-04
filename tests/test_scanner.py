from __future__ import annotations

from pathlib import Path
from unittest import mock

from readme_forge.scanner import MAX_FILE_SIZE, scan_repo


def test_python_repo_files_collected(fixtures_dir: Path) -> None:
    result = scan_repo(fixtures_dir / "python_repo")
    relative_paths = {f.relative_path for f in result.files}
    assert "pyproject.toml" in relative_paths
    assert "src/samplepy/main.py" in relative_paths
    assert "pyproject.toml" in result.manifest_contents


def test_gitignore_excludes_matched_paths(fixtures_dir: Path) -> None:
    result = scan_repo(fixtures_dir / "mixed_repo")
    relative_paths = {f.relative_path for f in result.files}
    assert "ignored_dir/should_not_appear.py" not in relative_paths
    assert "app.py" in relative_paths
    assert "app.js" in relative_paths


def test_secret_file_skipped_and_noted(fixtures_dir: Path) -> None:
    result = scan_repo(fixtures_dir / "mixed_repo")
    relative_paths = {f.relative_path for f in result.files}
    assert "credentials" not in relative_paths
    assert any("credentials" in note for note in result.notes)


def test_large_file_skipped_and_noted(tmp_path: Path) -> None:
    big_file = tmp_path / "big.bin"
    big_file.write_bytes(b"0" * (MAX_FILE_SIZE + 1))
    result = scan_repo(tmp_path)
    relative_paths = {f.relative_path for f in result.files}
    assert "big.bin" not in relative_paths
    assert any("large file" in note for note in result.notes)


def test_unreadable_file_skipped_and_noted(tmp_path: Path) -> None:
    (tmp_path / "readable.py").write_text("x = 1\n")
    real_stat = Path.stat

    def flaky_stat(self: Path, *args: object, **kwargs: object):
        if self.name == "readable.py":
            raise OSError("permission denied")
        return real_stat(self, *args, **kwargs)

    with mock.patch("pathlib.Path.stat", flaky_stat):
        result = scan_repo(tmp_path)
    assert result.files == []
    assert any("unreadable file" in note for note in result.notes)


def test_empty_directory_yields_no_files(tmp_path: Path) -> None:
    result = scan_repo(tmp_path)
    assert result.files == []
    assert result.manifest_contents == {}


def test_symlink_outside_repo_not_read(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "private.json"
    secret.write_text('{"name": "leaked"}', encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").symlink_to(secret)

    result = scan_repo(repo)

    assert "package.json" not in result.manifest_contents
    assert "package.json" not in {f.relative_path for f in result.files}
    assert any("symlink outside repo" in note for note in result.notes)


def test_symlink_inside_repo_still_scanned(tmp_path: Path) -> None:
    (tmp_path / "real.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "alias.py").symlink_to(tmp_path / "real.py")

    result = scan_repo(tmp_path)

    assert {"real.py", "alias.py"} <= {f.relative_path for f in result.files}
