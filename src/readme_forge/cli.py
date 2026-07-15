"""Command-line entry point for readme-forge."""

import click

from readme_forge import __version__


@click.command()
@click.argument("path", required=False, default=".")
@click.version_option(version=__version__, prog_name="readme-forge")
def main(path: str) -> None:
    """Scan PATH and draft a README.md using the Anthropic Claude API."""
    click.echo(f"readme-forge scaffold: would scan {path}")


if __name__ == "__main__":
    main()
