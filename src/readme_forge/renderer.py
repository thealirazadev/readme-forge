"""Rich-based terminal output: summary recap, progress, and README preview."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from readme_forge.summary import RepoSummary


def make_console(color: bool, stderr: bool = False) -> Console:
    """Build a rich Console; color/highlighting are disabled when color is False."""
    return Console(no_color=not color, highlight=False, stderr=stderr)


def print_error(console: Console, message: str) -> None:
    """Print a one-line friendly error: red 'Error:' prefix when color is on, plain otherwise."""
    console.print(f"Error: {message}", style="bold red")


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


class WriteAction(Enum):
    """What the CLI should do after preview, per the design.md decision table."""

    WRITE = "write"
    PROMPT = "prompt"
    SKIP = "skip"


def decide_write_action(exists: bool, overwrite: bool, dry_run: bool) -> WriteAction:
    """Decide the write action for the current flags and target-file state."""
    if dry_run:
        return WriteAction.SKIP
    if exists and not overwrite:
        return WriteAction.PROMPT
    return WriteAction.WRITE


def confirm_overwrite(target_path: str, interactive: bool) -> bool:
    """Ask to overwrite an existing file. Returns False without prompting if non-interactive."""
    if not interactive:
        return False
    return click.confirm(f"{target_path} already exists. Overwrite?", default=False)
