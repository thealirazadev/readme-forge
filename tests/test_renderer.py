"""Tests for renderer.py: console setup, recap/preview rendering, progress spinner."""

from __future__ import annotations

import io

from rich.console import Console

from readme_forge.renderer import (
    make_console,
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
