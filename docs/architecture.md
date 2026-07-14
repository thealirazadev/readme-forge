# Architecture: readme-forge

## Overview

readme-forge is a single-process CLI. It reads a local repository, produces a structured summary, asks the Anthropic Claude API to draft a README from that summary, previews the result, and writes it after confirmation. There is no server and no persistent storage beyond the written file and an optional config file.

## End-to-end flow

```
scan repo
  -> detect languages / manifests / scripts / structure
  -> build a structured summary (bounded, secret-free)
  -> call the Claude API with the summary + requested sections
  -> receive a drafted README (Markdown)
  -> preview in the terminal
  -> confirm-before-write (unless --dry-run; honor --overwrite / --output)
  -> write README.md
```

Step by step:

1. **Resolve config and args.** Parse CLI flags (click), load `.env`, resolve model id and sections. Validate the target path.
2. **Scan.** Walk the directory. Apply ignore rules (`.gitignore` plus built-in ignores), size limits, and a binary/secret skip list. Collect file paths, extensions, and the contents of recognized manifest files only.
3. **Detect.** Compute language weights from extension counts. Parse each recognized manifest (JSON, TOML, YAML) for name, description, scripts, entry points, dependencies.
4. **Summarize.** Assemble a `RepoSummary` object. Enforce the total size cap by truncating lists and long strings.
5. **Draft.** Serialize the summary into a prompt, call the Claude API (`anthropic` SDK). Show a progress spinner during the call.
6. **Preview.** Render the returned Markdown with rich. Show target path and whether it exists.
7. **Write.** If `--dry-run`, stop after preview. Otherwise, if the target exists and `--overwrite` is not set, ask for confirmation. Write on approval.

## Proposed folder / file tree

```
readme-forge/
  pyproject.toml            # packaging, pinned deps, console entry point, tool config
  README.md
  .env.example
  .gitignore
  src/
    readme_forge/
      __init__.py           # version string
      cli.py                # click entry point `readme-forge`, flag wiring, exit codes
      config.py             # Config dataclass; env + .env + flag resolution; defaults
      scanner.py            # directory walk, ignore rules, size/secret/binary skipping
      detect.py             # language weighting + manifest parsing
      summary.py            # RepoSummary dataclass + builder + size capping
      api.py                # Claude API client wrapper, prompt build, error mapping
      renderer.py           # rich preview, progress, confirm-before-write, NO_COLOR
      errors.py             # exception types + friendly-message mapping + exit codes
      logging_setup.py      # quiet/verbose logging config
  tests/
    conftest.py             # fixtures: fake repos, mocked anthropic client
    fixtures/               # sample repos (python, node, go, empty, mixed)
    test_scanner.py
    test_detect.py
    test_summary.py
    test_api.py             # uses mocked client only
    test_cli.py             # click CliRunner, covers happy + unhappy paths
    test_renderer.py
  docs/
    PRD.md architecture.md rules.md design.md phases.md testing.md memory.md launch-checklist.md
```

## Tech stack with rationale

- **Python 3.10+** — target language; 3.10 gives `match`, modern typing, and wide availability.
- **click** — declarative flags, subcommand-free single command, built-in `CliRunner` for tests, good help text.
- **rich** — colored output, progress spinners, Markdown preview, and it honors `NO_COLOR` and non-TTY detection out of the box.
- **anthropic** (official SDK) — typed client for the Claude API, handles retries and surfaces typed errors we can map to friendly messages.
- **pathspec** — parse `.gitignore` patterns correctly (gitwildmatch) instead of hand-rolling glob logic.
- **tomllib** (stdlib, 3.11+) with **tomli** fallback for 3.10 — parse `pyproject.toml`, `Cargo.toml`, `go.mod`-adjacent TOML.
- **PyYAML** — parse `pubspec.yaml` and other YAML manifests.
- **python-dotenv** — load `.env` for local development without polluting the real environment.
- **pytest** — test runner; the Anthropic client is mocked so tests never hit the network.
- **Ruff + Black** — lint and format; fast, standard, low-config.

## Data model

### RepoSummary (the single input to the model)

```
RepoSummary:
  root_name: str                 # basename of the scanned directory
  file_count: int                # total files considered (post-ignore)
  languages: list[LanguageStat]  # sorted desc by weight, capped to top N
  manifests: list[Manifest]      # parsed recognized manifests
  scripts: dict[str, str]        # merged declared scripts (name -> command), capped
  entry_points: list[str]        # detected entry points (e.g. main.py, index.js, cmd/*)
  top_level: list[str]           # top-level dirs and notable files, capped
  has_tests: bool                # heuristic (tests/ dir, *_test.*, test_*.py)
  has_ci: bool                   # .github/workflows, .gitlab-ci.yml, etc.
  license_hint: str | None       # from LICENSE file or manifest license field
  notes: list[str]               # scan notes (e.g. "skipped 3 large binaries")

LanguageStat:
  name: str                      # e.g. "Python"
  file_count: int
  weight: float                  # 0..1, share of considered code files

Manifest:
  kind: str                      # "package.json" | "pyproject.toml" | "go.mod" | ...
  path: str                      # repo-relative
  name: str | None
  description: str | None
  version: str | None
  scripts: dict[str, str]
  dependencies: list[str]        # names only, capped
```

The summary is size-bounded. All lists are capped (documented caps in `summary.py`), long strings are truncated with an ellipsis marker, and the serialized JSON has a hard total cap. This keeps prompts small and cost predictable regardless of repo size.

### Config

```
Config:
  target_path: Path              # repo to scan
  output_path: Path              # where to write (default <target>/README.md)
  overwrite: bool
  dry_run: bool
  model: str                     # resolved: --model > README_FORGE_MODEL > default
  sections: list[str]            # resolved from --sections or a default set
  quiet: bool
  verbose: bool
  color: bool                    # resolved from NO_COLOR + TTY detection
```

Recognized manifest kinds (initial set): `package.json`, `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`, `composer.json`, `pubspec.yaml`, `go.mod`, `Cargo.toml`, `Gemfile`, `build.gradle`, `pom.xml`.

Default sections: `overview`, `features`, `tech stack`, `prerequisites`, `installation`, `usage`, `project structure`, `license`.

## Where state lives

- **No persistent state** beyond the written `README.md`.
- **Optional config file** (backlog, not Phase 1): a project-local `.readme-forge.toml` may hold default sections/model. If present it is read at startup; flags always win.
- **Runtime state** is in-memory only (Config, RepoSummary).
- **Secrets** live only in the environment / `.env`, never written anywhere by the tool.

## External dependencies and required environment variables

External services:

- **Anthropic Claude API** — the only external network dependency. Called through the `anthropic` Python SDK. A default model id is used unless overridden; a reasonable current default is `claude-sonnet-4-5-20250929` (override with `--model` or `README_FORGE_MODEL`).

Environment variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Yes | Authenticates calls to the Claude API. Read from env or `.env`. Never logged. |
| `README_FORGE_MODEL` | No | Overrides the default Claude model id. `--model` overrides this. |
| `NO_COLOR` | No | If set (any value), disables ANSI color output. |

What is sent to the API: only the bounded `RepoSummary` (language stats, parsed manifest fields, script names/commands, structure hints) plus the list of requested sections. Raw file contents other than recognized manifests are never sent. Files matched by ignore rules, secrets, and large binaries are never read and therefore never sent.
