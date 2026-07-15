"""Command-line entry point for readme-forge."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from readme_forge import __version__
from readme_forge.detect import detect_languages, parse_manifests
from readme_forge.errors import NotARepoError, ReadmeForgeError, format_error
from readme_forge.scanner import scan_repo
from readme_forge.summary import RepoSummary, build_summary


def _build_summary(path: str) -> RepoSummary:
    target = Path(path)
    if not target.is_dir():
        raise NotARepoError(f"path is not a directory: {path}")

    scan_result = scan_repo(target)
    languages = detect_languages(scan_result.files)
    manifests = parse_manifests(scan_result.manifest_contents, scan_result.notes)
    return build_summary(target, scan_result.files, languages, manifests, scan_result.notes)


@click.command()
@click.argument("path", required=False, default=".")
@click.option(
    "--summary-json",
    is_flag=True,
    hidden=True,
    help="Print the scanned RepoSummary as JSON and exit (debug/inspection).",
)
@click.version_option(version=__version__, prog_name="readme-forge")
def main(path: str, summary_json: bool) -> None:
    """Scan PATH and draft a README.md using the Anthropic Claude API."""
    try:
        summary = _build_summary(path)
    except ReadmeForgeError as exc:
        click.echo(format_error(exc.message), err=True)
        sys.exit(exc.exit_code)

    if summary_json:
        click.echo(summary.to_json())
        sys.exit(0)

    if summary.file_count == 0:
        click.echo("Repository appears to be empty; nothing to summarize.")
        sys.exit(0)

    click.echo(summary.to_json())


if __name__ == "__main__":
    main()
