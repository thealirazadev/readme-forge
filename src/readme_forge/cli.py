"""Command-line entry point for readme-forge."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import anthropic
import click
from dotenv import load_dotenv

from readme_forge import __version__
from readme_forge.api import draft_readme
from readme_forge.config import resolve_color, resolve_model, resolve_sections
from readme_forge.detect import detect_languages, parse_manifests
from readme_forge.errors import (
    ApiKeyMissingError,
    NotARepoError,
    OverwriteRefused,
    ReadmeForgeError,
    UsageError,
    WriteError,
    map_anthropic_error,
)
from readme_forge.logging_setup import configure_logging
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
from readme_forge.scanner import scan_repo
from readme_forge.summary import RepoSummary, build_summary


def _exit_with_error(err_console, message: str, exit_code: int, verbose: bool) -> None:
    print_error(err_console, message)
    if verbose:
        traceback.print_exc()
    sys.exit(exit_code)


def _build_summary(console, path: str, quiet: bool) -> RepoSummary:
    target = Path(path)
    if not target.is_dir():
        raise NotARepoError(f"path is not a directory: {path}")

    with progress_step(console, quiet, "Scanning files..."):
        scan_result = scan_repo(target)
    with progress_step(console, quiet, "Detecting languages..."):
        languages = detect_languages(scan_result.files)
    with progress_step(console, quiet, "Parsing manifests..."):
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
    "--overwrite",
    is_flag=True,
    help="Replace an existing README at the output path without prompting.",
)
@click.option(
    "--output",
    "output",
    default=None,
    type=click.Path(path_type=Path),
    help="Where to write the generated README. Defaults to PATH/README.md.",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Minimal output: no progress or recap, only the preview and errors.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Detailed output: resolved config, scan notes, and full tracebacks on error.",
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
    overwrite: bool,
    output: Path | None,
    quiet: bool,
    verbose: bool,
    summary_json: bool,
) -> None:
    """Scan PATH and draft a README.md using the Anthropic Claude API."""
    color = resolve_color(sys.stdout.isatty())
    console = make_console(color=color)
    err_console = make_console(color=color, stderr=True)

    if quiet and verbose:
        _exit_with_error(
            err_console, "--quiet and --verbose are mutually exclusive", UsageError.exit_code, False
        )

    configure_logging(quiet, verbose)

    try:
        _run(
            console,
            err_console,
            path,
            model,
            sections,
            dry_run,
            overwrite,
            output,
            quiet,
            verbose,
            summary_json,
        )
    except SystemExit:
        raise
    except Exception as exc:  # last-resort guard: never a bare traceback by default
        _exit_with_error(err_console, f"unexpected error: {exc}", 1, verbose)


def _run(
    console,
    err_console,
    path: str,
    model: str | None,
    sections: str | None,
    dry_run: bool,
    overwrite: bool,
    output: Path | None,
    quiet: bool,
    verbose: bool,
    summary_json: bool,
) -> None:
    try:
        summary = _build_summary(console, path, quiet)
    except ReadmeForgeError as exc:
        _exit_with_error(err_console, exc.message, exc.exit_code, verbose)

    if summary_json:
        click.echo(summary.to_json())
        sys.exit(0)

    if summary.file_count == 0:
        click.echo("Repository appears to be empty; nothing to summarize.")
        sys.exit(0)

    if not quiet:
        render_summary_recap(console, summary)

    resolved_model = resolve_model(model)
    resolved_sections = resolve_sections(sections)
    output_path = output if output is not None else Path(path) / "README.md"

    if verbose:
        console.print(f"Resolved model: {resolved_model}")
        console.print(f"Resolved sections: {', '.join(resolved_sections)}")
        console.print(f"Output path: {output_path}")

    try:
        api_key = _get_api_key()
        with progress_step(console, quiet, "Drafting README with Claude..."):
            markdown_text = draft_readme(summary, resolved_sections, resolved_model, api_key)
    except anthropic.APIError as exc:
        friendly = map_anthropic_error(exc)
        _exit_with_error(err_console, friendly.message, friendly.exit_code, verbose)
    except ReadmeForgeError as exc:
        _exit_with_error(err_console, exc.message, exc.exit_code, verbose)

    exists = output_path.exists()
    render_preview(console, markdown_text, str(output_path), exists)

    try:
        action = decide_write_action(exists, overwrite, dry_run)
        if action is WriteAction.SKIP:
            click.echo("Dry run: nothing written.")
            sys.exit(0)
        if action is WriteAction.PROMPT:
            if not sys.stdin.isatty():
                raise OverwriteRefused(
                    f"{output_path} already exists; pass --overwrite to replace it"
                )
            if not confirm_overwrite(str(output_path), interactive=True):
                click.echo("Not overwriting; nothing written.")
                sys.exit(0)
        output_path.write_text(markdown_text, encoding="utf-8")
    except ReadmeForgeError as exc:
        _exit_with_error(err_console, exc.message, exc.exit_code, verbose)
    except OSError as exc:
        write_error = WriteError(f"could not write {output_path}: {exc}")
        _exit_with_error(err_console, write_error.message, write_error.exit_code, verbose)

    click.echo(f"OK: wrote {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
