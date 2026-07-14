# Memory: readme-forge

Working log for the project. Keep entries short and dated. Newest first within each section.

## Completed

- 2026-07-15: Planning documentation created (README, PRD, architecture, rules, design, phases, testing, memory, launch checklist, .env.example).

## In progress

- (nothing yet)

## Decisions log

- 2026-07-15: Model provider is the Anthropic Claude API via the official `anthropic` SDK; default model id `claude-sonnet-4-5-20250929`, overridable by `--model` and `README_FORGE_MODEL`.
- 2026-07-15: Only the bounded `RepoSummary` and requested sections are sent to the API; non-manifest file bodies, secrets, and large binaries are never read or sent.
- 2026-07-15: CLI built on click + rich; single command with a positional `PATH`; exit codes 0/1/2/3/4 as defined in design.md.
- 2026-07-15: Dependencies pinned with `==` and a committed lockfile for reproducible builds.
