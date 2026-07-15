"""Tests for renderer.py: console setup, recap/preview rendering, progress spinner."""

from __future__ import annotations

import io
from unittest import mock

from rich.console import Console

from readme_forge.renderer import (
    WriteAction,
    confirm_overwrite,
    decide_write_action,
    make_console,
    print_error,
    progress_step,
    render_preview,
    render_summary_recap,
)
from readme_forge.summary import RepoSummary


def test_make_console_disables_color_when_color_false() -> None:
    console = make_console(color=False)
    assert console.no_color is True


def test_make_console_enables_color_when_color_true() -> None:
    console = make_console(color=True)
    assert console.no_color is False


def test_make_console_stderr_binds_to_stderr_stream() -> None:
    console = make_console(color=True, stderr=True)
    assert console.stderr is True


def _capturing_console() -> Console:
    return Console(file=io.StringIO(), no_color=True, highlight=False, width=100)


def test_render_summary_recap_shows_key_facts() -> None:
    console = _capturing_console()
    summary = RepoSummary(
        root_name="sample",
        file_count=5,
        has_tests=True,
        has_ci=False,
    )
    render_summary_recap(console, summary)
    output = console.file.getvalue()
    assert "none detected" in output
    assert "5" in output
    assert "yes" in output


def test_render_preview_shows_target_status_and_markdown() -> None:
    console = _capturing_console()
    render_preview(console, "# Title\n", "/repo/README.md", exists=True)
    output = console.file.getvalue()
    assert "/repo/README.md" in output
    assert "(exists)" in output


def test_render_preview_shows_new_file_when_absent() -> None:
    console = _capturing_console()
    render_preview(console, "# Title\n", "/repo/README.md", exists=False)
    output = console.file.getvalue()
    assert "(new file)" in output


def test_progress_step_runs_body_and_is_silent_under_quiet() -> None:
    console = _capturing_console()
    ran = False
    with progress_step(console, quiet=True, message="Working..."):
        ran = True
    assert ran
    assert console.file.getvalue() == ""


def test_progress_step_runs_body_when_not_quiet() -> None:
    console = _capturing_console()
    ran = False
    with progress_step(console, quiet=False, message="Working..."):
        ran = True
    assert ran


def test_decide_write_action_dry_run_always_skips() -> None:
    assert decide_write_action(exists=False, overwrite=False, dry_run=True) is WriteAction.SKIP
    assert decide_write_action(exists=True, overwrite=True, dry_run=True) is WriteAction.SKIP


def test_decide_write_action_new_file_writes_directly() -> None:
    assert decide_write_action(exists=False, overwrite=False, dry_run=False) is WriteAction.WRITE
    assert decide_write_action(exists=False, overwrite=True, dry_run=False) is WriteAction.WRITE


def test_decide_write_action_existing_file_without_overwrite_prompts() -> None:
    assert decide_write_action(exists=True, overwrite=False, dry_run=False) is WriteAction.PROMPT


def test_decide_write_action_existing_file_with_overwrite_writes() -> None:
    assert decide_write_action(exists=True, overwrite=True, dry_run=False) is WriteAction.WRITE


def test_confirm_overwrite_non_interactive_declines_without_prompting() -> None:
    with mock.patch("readme_forge.renderer.click.confirm") as confirm:
        result = confirm_overwrite("README.md", interactive=False)
    assert result is False
    confirm.assert_not_called()


def test_confirm_overwrite_interactive_delegates_to_click_confirm() -> None:
    with mock.patch("readme_forge.renderer.click.confirm", return_value=True) as confirm:
        result = confirm_overwrite("README.md", interactive=True)
    assert result is True
    confirm.assert_called_once()
    args, kwargs = confirm.call_args
    assert "README.md" in args[0]
    assert kwargs["default"] is False


def test_print_error_includes_prefix_and_message() -> None:
    console = _capturing_console()
    print_error(console, "something went wrong")
    output = console.file.getvalue()
    assert "Error: something went wrong" in output
