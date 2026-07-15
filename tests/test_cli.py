"""End-to-end CLI tests via click's CliRunner. The Claude client is always mocked."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import anthropic
import pytest
from click.testing import CliRunner

from readme_forge.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_not_a_directory_exits_2(runner: CliRunner, fixtures_dir: Path) -> None:
    target = fixtures_dir / "python_repo" / "pyproject.toml"
    result = runner.invoke(main, [str(target)])
    assert result.exit_code == 2
    assert "not a directory" in result.output


def test_empty_repo_exits_0(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


def test_missing_api_key_exits_3(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = runner.invoke(main, [str(fixtures_dir / "python_repo")])
    assert result.exit_code == 3
    assert "ANTHROPIC_API_KEY" in result.output


def test_dry_run_previews_and_writes_nothing(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with mock.patch("readme_forge.cli.draft_readme", return_value="# Sample README\n"):
        result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--dry-run"])
    assert result.exit_code == 0
    assert "Dry run: nothing written." in result.output
    assert not (fixtures_dir / "python_repo" / "README.md").exists()


def test_network_error_exits_3_with_friendly_message(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    error = anthropic.APIConnectionError(request=mock.Mock())
    with mock.patch("readme_forge.cli.draft_readme", side_effect=error):
        result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--dry-run"])
    assert result.exit_code == 3
    assert "Traceback" not in result.output
    assert "network" in result.output.lower()


def test_invalid_key_exits_3_with_friendly_message(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    response = mock.Mock(status_code=401)
    error = anthropic.AuthenticationError("invalid key", response=response, body=None)
    with mock.patch("readme_forge.cli.draft_readme", side_effect=error):
        result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--dry-run"])
    assert result.exit_code == 3
    assert "invalid" in result.output.lower()


def test_new_file_writes_without_prompt(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    (tmp_path / "app.py").write_text("print('hi')\n")
    with mock.patch("readme_forge.cli.draft_readme", return_value="# New\n"):
        result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "OK: wrote" in result.output
    assert (tmp_path / "README.md").read_text() == "# New\n"


def test_existing_readme_without_overwrite_non_interactive_exits_4(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    (tmp_path / "app.py").write_text("print('hi')\n")
    (tmp_path / "README.md").write_text("old content\n")
    with mock.patch("readme_forge.cli.draft_readme", return_value="# New\n"):
        result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 4
    assert "--overwrite" in result.output
    assert (tmp_path / "README.md").read_text() == "old content\n"


def test_existing_readme_with_overwrite_writes_without_prompt(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    (tmp_path / "app.py").write_text("print('hi')\n")
    (tmp_path / "README.md").write_text("old content\n")
    with mock.patch("readme_forge.cli.draft_readme", return_value="# New\n"):
        result = runner.invoke(main, [str(tmp_path), "--overwrite"])
    assert result.exit_code == 0
    assert (tmp_path / "README.md").read_text() == "# New\n"


def test_output_flag_writes_to_custom_path(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    (tmp_path / "app.py").write_text("print('hi')\n")
    custom_output = tmp_path / "docs" / "README.md"
    custom_output.parent.mkdir()
    with mock.patch("readme_forge.cli.draft_readme", return_value="# New\n"):
        result = runner.invoke(main, [str(tmp_path), "--output", str(custom_output)])
    assert result.exit_code == 0
    assert custom_output.read_text() == "# New\n"
    assert not (tmp_path / "README.md").exists()


def test_quiet_and_verbose_together_is_usage_error(runner: CliRunner, fixtures_dir: Path) -> None:
    result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--quiet", "--verbose"])
    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_quiet_suppresses_recap(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with mock.patch("readme_forge.cli.draft_readme", return_value="# S\n"):
        result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--dry-run", "--quiet"])
    assert result.exit_code == 0
    assert "Primary language" not in result.output


def test_verbose_shows_resolved_config(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with mock.patch("readme_forge.cli.draft_readme", return_value="# S\n"):
        result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--dry-run", "--verbose"])
    assert result.exit_code == 0
    assert "Resolved model" in result.output
    assert "Resolved sections" in result.output


def test_unexpected_error_exits_1_without_traceback_by_default(
    runner: CliRunner, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with mock.patch("readme_forge.cli.draft_readme", side_effect=RuntimeError("boom")):
        result = runner.invoke(main, [str(fixtures_dir / "python_repo"), "--dry-run"])
    assert result.exit_code == 1
    assert "unexpected error" in result.output.lower()
    assert "Traceback" not in result.output
