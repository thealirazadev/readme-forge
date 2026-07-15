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
