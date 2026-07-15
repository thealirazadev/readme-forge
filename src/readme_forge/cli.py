"""Command-line entry point for readme-forge."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import anthropic
import click
from dotenv import load_dotenv

from readme_forge import __version__
from readme_forge.api import draft_readme
from readme_forge.config import resolve_model, resolve_sections
from readme_forge.detect import detect_languages, parse_manifests
from readme_forge.errors import (
    ApiKeyMissingError,
    NotARepoError,
    ReadmeForgeError,
    format_error,
    map_anthropic_error,
)
from readme_forge.renderer import (
    make_console,
    progress_step,
    render_preview,
    render_summary_recap,
)
from readme_forge.scanner import scan_repo
from readme_forge.summary import RepoSummary, build_summary


def _build_summary(console, path: str) -> RepoSummary:
    target = Path(path)
    if not target.is_dir():
        raise NotARepoError(f"path is not a directory: {path}")

    with progress_step(console, False, "Scanning files..."):
        scan_result = scan_repo(target)
    with progress_step(console, False, "Detecting languages..."):
        languages = detect_languages(scan_result.files)
    with progress_step(console, False, "Parsing manifests..."):
        manifests = parse_manifests(scan_result.manifest_contents, scan_result.notes)
    return build_summary(target, scan_result.files, languages, manifests, scan_result.notes)


def _get_api_key() -> str:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ApiKeyMissingError("set ANTHROPIC_API_KEY or add it to .env to draft a README")
    return api_key


@click.command()
@click.argument("path", required=False, default=".")
@click.option(
    "--model",
    default=None,
    help="Claude model id. Precedence: --model > README_FORGE_MODEL > built-in default.",
)
@click.option(
    "--sections",
    default=None,
    help="Comma-separated section list, e.g. 'overview,install,usage,license'.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Scan, draft, and preview the README, but write nothing.",
)
@click.option(
    "--summary-json",
    is_flag=True,
    hidden=True,
    help="Print the scanned RepoSummary as JSON and exit (debug/inspection).",
)
@click.version_option(version=__version__, prog_name="readme-forge")
def main(
    path: str,
    model: str | None,
    sections: str | None,
    dry_run: bool,
    summary_json: bool,
) -> None:
    """Scan PATH and draft a README.md using the Anthropic Claude API."""
    console = make_console(color=True)

    try:
        summary = _build_summary(console, path)
    except ReadmeForgeError as exc:
        click.echo(format_error(exc.message), err=True)
        sys.exit(exc.exit_code)

    if summary_json:
        click.echo(summary.to_json())
        sys.exit(0)

    if summary.file_count == 0:
        click.echo("Repository appears to be empty; nothing to summarize.")
        sys.exit(0)

    render_summary_recap(console, summary)

    resolved_model = resolve_model(model)
    resolved_sections = resolve_sections(sections)

    try:
        api_key = _get_api_key()
        with progress_step(console, False, "Drafting README with Claude..."):
            markdown_text = draft_readme(summary, resolved_sections, resolved_model, api_key)
    except anthropic.APIError as exc:
        friendly = map_anthropic_error(exc)
        click.echo(format_error(friendly.message), err=True)
        sys.exit(friendly.exit_code)
    except ReadmeForgeError as exc:
        click.echo(format_error(exc.message), err=True)
        sys.exit(exc.exit_code)

    output_path = Path(path) / "README.md"
    render_preview(console, markdown_text, str(output_path), output_path.exists())

    # Phase 2 never writes; the write gate lands with --overwrite/--output support.
    click.echo("Dry run: nothing written." if dry_run else "Preview only: nothing written yet.")
    sys.exit(0)


if __name__ == "__main__":
    main()
