# Memory: readme-forge

Working log for the project. Keep entries short and dated. Newest first within each section.

## Completed

- 2026-07-15: Planning documentation created (README, PRD, architecture, rules, design, phases, testing, memory, launch checklist, .env.example).
- 2026-07-15: Phase 1 (scan and structured summary) implemented and tested: scanner, detect, summary, CLI `--summary-json` debug path.
- 2026-07-16: Phase 2 (draft via Claude API + preview + dry-run) completed: `renderer.py` (preview panel, progress spinner), `config.py` (model/sections/color resolution), CLI wired to scan, draft, and preview with progress spinners; API errors mapped to friendly messages/exit code 3. Covered by `test_api.py`, `test_renderer.py`, `test_cli.py` with the Anthropic client mocked throughout.
- 2026-07-16: Phase 3 (write gate, overwrite safety, UX polish) completed: confirm-before-write gate (`decide_write_action`/`confirm_overwrite` in renderer.py, `WriteError`/`OverwriteRefused` in errors.py), `--output`, `NO_COLOR`/non-TTY color resolution, `--quiet`/`--verbose` (via `logging_setup.py`, scoped to the `readme_forge` logger only), finalized exit codes with a stderr rich console for friendly red-on-color errors, a last-resort exception guard (exit 1, no bare traceback unless `--verbose`), and `--help` usage examples. Full write-gate/overwrite/non-interactive-decline test coverage added.
- 2026-07-16: Added `requirements.lock` (pinned direct + transitive dependency set) per rules.md; was missing since the initial scaffold commit.

- 2026-07-17: Ran the launch checklist (docs/launch-checklist.md) end to end. Local `.venv` had a stale symlink to a macOS homebrew Python path from a prior machine; recreated it with `python3 -m venv .venv` on this host. `pip install -e ".[dev]"` succeeds (slow network, several minutes, no functional issue). `ruff check .`, `black --check .`, and `pytest` (53 tests) all pass clean. `python -m build` produces both wheel and sdist; `twine check dist/*` passes. Manually exercised the CLI: not-a-directory (exit 2), empty repo (exit 0), missing API key (exit 3), a real network call with a fake key correctly mapped 401 to "invalid ANTHROPIC_API_KEY" (exit 3), dry-run (writes nothing), new-file write, existing-README-without-overwrite under non-interactive stdin (exit 4, matches CliRunner behavior since piped stdin is never a tty), `--overwrite`, `--output`, `NO_COLOR`/non-TTY (no ANSI codes), `--quiet`, `--verbose`, and `--quiet`+`--verbose` conflict (exit 2). Checked `.env.example` (dummy key only), LICENSE (MIT, present), pyproject.toml metadata (complete), commit history (all Conventional Commits), and no emoji/authorship attribution anywhere in src/tests/docs. Ticked every launch-checklist box except the "PyPI publish" upload/tag items, which require real PyPI credentials not available here.

## In progress

- Nothing outstanding from the implementation phases. Remaining launch-checklist work is PyPI credential-gated: version bump/tag, TestPyPI upload, PyPI upload. Needs a human with publish access.

## Decisions log

- 2026-07-15: Model provider is the Anthropic Claude API via the official `anthropic` SDK; default model id `claude-sonnet-4-5-20250929`, overridable by `--model` and `README_FORGE_MODEL`.
- 2026-07-15: Only the bounded `RepoSummary` and requested sections are sent to the API; non-manifest file bodies, secrets, and large binaries are never read or sent.
- 2026-07-15: CLI built on click + rich; single command with a positional `PATH`; exit codes 0/1/2/3/4 as defined in design.md.
- 2026-07-15: Dependencies pinned with `==` and a committed lockfile for reproducible builds.
- 2026-07-16: Modules are built standalone first and wired into `cli.py` in a later, dedicated commit (matches the existing phase-1 pattern for `api.py`/`errors.py`) to avoid intermediate commits with dead/unused code.
- 2026-07-16: `--quiet`/`--verbose` configure only the `readme_forge` logger (not the root logger via `logging.basicConfig`) — an earlier draft using `basicConfig` leaked third-party library DEBUG output (markdown-it internals) into `--verbose` runs.
- 2026-07-16: Friendly errors are printed through a dedicated stderr `rich.Console` (`make_console(color, stderr=True)`) so the red "Error:" prefix is automatic under color and plain otherwise, matching design.md without hand-rolled ANSI codes.
- 2026-07-16: A top-level `except Exception` guard in `cli.py` wraps the whole run so a genuine bug degrades to exit code 1 with a friendly message instead of a raw traceback; `--verbose` still prints the traceback.

- 2026-11-09: Manual checklists run against real models (Sonnet/Haiku 5.5 via a local
  Anthropic-Messages shim that calls the Claude Code CLI; outside the repo) on real repos
  (quotaguard, taskboard) and scratch fixtures. Drafts were grounded in the real manifests,
  scripts, and entry points. Two fixes: the summary's `top_level` listed the raw directory, so
  gitignored paths (node_modules, dist, build), secret files (.env), and skipped binaries reached
  the prompt even though the scanner had excluded them; it now lists only top-level names of
  scanned files. `--output docs/README.md` into a missing folder failed with exit 1; parent
  folders are now created. Default model updated to `claude-sonnet-5-5` (flagged
  architecture.md edit: the id only). Piped "n" at the overwrite prompt exits 4 by design
  (non-interactive stdin), the interactive decline path is covered by tests.
