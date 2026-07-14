# PRD: readme-forge

## What we're building

readme-forge is a Python command-line tool that inspects a local code repository and drafts a `README.md` for it. It scans the tree, detects languages and manifest files, extracts scripts and entry points, builds a compact structured summary, and sends that summary to the Anthropic Claude API to draft a README with standard sections. The user sees a colored preview and confirms before anything is written. The tool never overwrites an existing README without an explicit `--overwrite` flag or an interactive confirmation.

## Target user

Developers and maintainers who have a working repository but a missing, thin, or stale `README.md`. They want a solid first draft that reflects what the code actually contains, produced in one command, that they can edit rather than write from scratch. They are comfortable in a terminal and have (or can get) an Anthropic API key.

## Core features (prioritized)

1. **Repo scan and detection.** Walk the repo, respect `.gitignore`, skip secrets and large binaries, detect languages by extension, and identify manifest files. Highest priority; nothing else works without it.
2. **Structured summary.** Turn raw scan results into a compact, bounded, structured summary object (languages with weights, manifests with parsed fields, scripts, entry points, top-level structure). This is the single input to the model.
3. **README drafting via Claude API.** Send the summary and requested sections to the Claude API and receive Markdown. Handle network, rate-limit, and invalid-key errors gracefully.
4. **Preview and confirm-before-write.** Render the draft in the terminal, then ask to write. Respect `--dry-run`, `--overwrite`, `--output`.
5. **CLI UX polish.** Progress indicators, `--quiet`/`--verbose`, `NO_COLOR`, meaningful exit codes, `--model`, `--sections`.

## Non-goals

- No editing or "improving" of existing prose beyond generating a fresh draft.
- No multi-file documentation generation (no wiki, no CONTRIBUTING, no docs site).
- No support for remote repositories or git hosting APIs; local path only.
- No persistent database, server, or web UI.
- No automatic commit or push of the generated README.
- No model provider other than Anthropic Claude.
- No language-specific deep static analysis (we read manifests and structure, not ASTs).
- No streaming edit/patch of an existing README; we produce a whole document.

## Success criteria per core feature

### Repo scan and detection
- Running against a known fixture repo detects the correct primary language and lists the expected manifest files.
- Paths matched by `.gitignore` are excluded from the summary.
- Files larger than the configured binary/size threshold and known secret files (for example `.env`, `*.pem`, `id_rsa`) are never read or sent.
- A path that is not a directory, or an empty directory, produces a friendly error or a clearly-labeled empty summary, not a crash.

### Structured summary
- The summary is deterministic for a fixed input tree (same tree in, same summary out).
- The summary is size-bounded: total serialized size stays under a documented cap regardless of repo size.
- Parsed manifest fields (name, description, scripts, dependencies) appear in the summary when present in the source manifest.

### README drafting via Claude API
- With the API mocked, a valid summary yields a Markdown document containing the requested sections.
- Network failure, HTTP 429 (rate limit), and HTTP 401 (invalid key) each produce a distinct friendly message and a non-zero exit code, never a raw traceback (unless `--verbose`).
- The API key is read from the environment or `.env` and never printed or logged.

### Preview and confirm-before-write
- The draft is shown before any write.
- Without `--overwrite`, an existing README at the target path is never replaced without an explicit "yes" confirmation; declining exits cleanly with code 0 and writes nothing.
- `--dry-run` prints the draft and writes nothing, even with `--overwrite`.
- `--output PATH` controls the written file location.

### CLI UX polish
- `NO_COLOR` set, or a non-TTY stdout, disables ANSI color; all information remains readable without color.
- `--quiet` suppresses progress and non-essential output; `--verbose` adds scan decisions and error detail.
- Exit codes are documented and consistent (see design.md): 0 success/declined, 1 runtime error, 2 usage error, 3 API error, 4 refused overwrite conflict.
- `readme-forge --help` lists every flag with a one-line description.
