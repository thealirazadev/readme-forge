# Memory: readme-forge

Working log for the project. Keep entries short and dated. Newest first within each section.

## Completed

- 2026-07-15: Planning documentation created (README, PRD, architecture, rules, design, phases, testing, memory, launch checklist, .env.example).
- 2026-07-15: Phase 1 (scan and structured summary) implemented and tested: scanner, detect, summary, CLI `--summary-json` debug path.
- 2026-07-16: Phase 2 (draft via Claude API + preview + dry-run) completed: `renderer.py` (preview panel, progress spinner), `config.py` (model/sections/color resolution), CLI wired to scan, draft, and preview with progress spinners; API errors mapped to friendly messages/exit code 3. Covered by `test_api.py`, `test_renderer.py`, `test_cli.py` with the Anthropic client mocked throughout.
- 2026-07-16: Phase 3 (write gate, overwrite safety, UX polish) completed: confirm-before-write gate (`decide_write_action`/`confirm_overwrite` in renderer.py, `WriteError`/`OverwriteRefused` in errors.py), `--output`, `NO_COLOR`/non-TTY color resolution, `--quiet`/`--verbose` (via `logging_setup.py`, scoped to the `readme_forge` logger only), finalized exit codes with a stderr rich console for friendly red-on-color errors, a last-resort exception guard (exit 1, no bare traceback unless `--verbose`), and `--help` usage examples. Full write-gate/overwrite/non-interactive-decline test coverage added.
- 2026-07-16: Added `requirements.lock` (pinned direct + transitive dependency set) per rules.md; was missing since the initial scaffold commit.

## In progress

- (nothing; all three phases from docs/phases.md are complete)

## Decisions log

- 2026-07-15: Model provider is the Anthropic Claude API via the official `anthropic` SDK; default model id `claude-sonnet-4-5-20250929`, overridable by `--model` and `README_FORGE_MODEL`.
- 2026-07-15: Only the bounded `RepoSummary` and requested sections are sent to the API; non-manifest file bodies, secrets, and large binaries are never read or sent.
- 2026-07-15: CLI built on click + rich; single command with a positional `PATH`; exit codes 0/1/2/3/4 as defined in design.md.
- 2026-07-15: Dependencies pinned with `==` and a committed lockfile for reproducible builds.
- 2026-07-16: Modules are built standalone first and wired into `cli.py` in a later, dedicated commit (matches the existing phase-1 pattern for `api.py`/`errors.py`) to avoid intermediate commits with dead/unused code.
- 2026-07-16: `--quiet`/`--verbose` configure only the `readme_forge` logger (not the root logger via `logging.basicConfig`) — an earlier draft using `basicConfig` leaked third-party library DEBUG output (markdown-it internals) into `--verbose` runs.
- 2026-07-16: Friendly errors are printed through a dedicated stderr `rich.Console` (`make_console(color, stderr=True)`) so the red "Error:" prefix is automatic under color and plain otherwise, matching design.md without hand-rolled ANSI codes.
- 2026-07-16: A top-level `except Exception` guard in `cli.py` wraps the whole run so a genuine bug degrades to exit code 1 with a friendly message instead of a raw traceback; `--verbose` still prints the traceback.
