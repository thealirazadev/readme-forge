# readme-forge

readme-forge is a command-line tool that scans a code repository, infers what it is (languages, package/manifest files, scripts, entry points, and structure), and drafts a `README.md` with standard sections using the Anthropic Claude API. You review a colored preview and confirm before anything is written to disk, so the tool never surprises you by overwriting your work.

## Features

- Walks a repository and detects languages by file extension and manifest files (`package.json`, `pyproject.toml`, `composer.json`, `pubspec.yaml`, `go.mod`, `Cargo.toml`, `Gemfile`, and similar).
- Extracts declared scripts, entry points, and dependencies from those manifests.
- Builds a compact structured summary of the repo (skips ignored paths, secrets, and large binaries).
- Drafts a `README.md` with standard sections via the Anthropic Claude API.
- Colored terminal output with progress while scanning and while calling the API.
- Preview of the generated README with a confirm-before-write step.
- Flags: `--output`, `--overwrite`, `--dry-run`, `--model`, `--sections`, `--quiet`, `--verbose`.
- Respects `NO_COLOR`; no meaning is conveyed by color alone.
- Never overwrites an existing README without `--overwrite` or an explicit confirmation.

## Tech stack

- Python 3.10+
- [click](https://click.palletsprojects.com/) for the CLI
- [rich](https://rich.readthedocs.io/) for colored output, progress, and preview
- [anthropic](https://pypi.org/project/anthropic/) SDK for the Claude API
- [pytest](https://docs.pytest.org/) for tests (the API is mocked)
- Ruff + Black for lint and formatting
- Packaged with `pyproject.toml` and a console entry point `readme-forge`

## Prerequisites

- Python 3.10 or newer.
- An Anthropic API key exported as `ANTHROPIC_API_KEY` (or placed in a local `.env`). See `.env.example`.

## Install

Recommended (isolated):

```
pipx install readme-forge
```

Or into the current environment:

```
pip install readme-forge
```

From source, for development:

```
pip install -e ".[dev]"
```

## Usage

Copy `.env.example` to `.env` and set your key, or export it:

```
export ANTHROPIC_API_KEY=sk-ant-your-key
```

Draft a README for the current directory (preview, then confirm):

```
readme-forge .
```

Common options:

```
readme-forge /path/to/repo --output README.md
readme-forge . --dry-run                 # print the draft, write nothing
readme-forge . --overwrite               # replace an existing README (still previews)
readme-forge . --model claude-sonnet-5-5
readme-forge . --sections "overview,install,usage,license"
readme-forge . --quiet                   # minimal output
readme-forge . --verbose                 # detailed logs, including scan decisions
```

Run `readme-forge --help` for the full list.

## Test steps

```
pip install -e ".[dev]"
ruff check .
black --check .
pytest
```

All of the above must pass. Tests never hit the network; the Anthropic API is mocked.

## Structure

```
readme-forge/
  src/readme_forge/     # package: CLI, scanner, summary, API client, renderer
  tests/                # pytest suite with fixture repos and a mocked API
  docs/                 # PRD, architecture, rules, design, phases, testing, memory, checklist
  pyproject.toml        # packaging + console entry point + pinned deps
  .env.example          # ANTHROPIC_API_KEY and optional README_FORGE_MODEL
  README.md
```

## License

License: MIT
