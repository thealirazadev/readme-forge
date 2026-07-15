"""Rich-based terminal output: summary recap, progress, and README preview."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from readme_forge.summary import RepoSummary


def make_console(color: bool) -> Console:
    """Build a rich Console; color/highlighting are disabled when color is False."""
    return Console(no_color=not color, highlight=False)


@contextmanager
def progress_step(console: Console, quiet: bool, message: str) -> Iterator[None]:
    """Show a spinner with `message` for the duration of the wrapped step.

    Under --quiet, no spinner is shown; the step still runs.
    """
    if quiet:
        yield
        return
    with console.status(message):
        yield


def render_summary_recap(console: Console, summary: RepoSummary) -> None:
    """Print a short recap table of the scanned repository before drafting."""
    table = Table(show_header=False, box=None)
    primary_language = summary.languages[0].name if summary.languages else "none detected"
    table.add_row("Primary language:", primary_language)
    table.add_row("Files scanned:", str(summary.file_count))
    table.add_row("Manifests found:", str(len(summary.manifests)))
    table.add_row("Tests detected:", "yes" if summary.has_tests else "no")
    table.add_row("CI detected:", "yes" if summary.has_ci else "no")
    console.print(table)


def render_preview(console: Console, markdown_text: str, target_path: str, exists: bool) -> None:
    """Print a one-line target status, then the drafted README in a bordered panel."""
    status = "(exists)" if exists else "(new file)"
    console.print(f"Target: {target_path} {status}")
    console.print(Panel(Markdown(markdown_text), title=target_path, expand=True))
