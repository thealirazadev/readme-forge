# Phases: readme-forge

Ship in the smallest useful increments. Each phase is independently shippable, builds, and passes tests. One commit per feature/task, in the order listed. Do not start a later phase's work in an earlier phase; anything extra goes to the Backlog at the bottom.

---

## Phase 1: Scan and structured summary (no API, no write)

The core value that everything depends on: walk a repo and produce a bounded, secret-free structured summary. Output the summary as JSON to stdout so it is verifiable without the API.

### Definition of done
- `readme-forge PATH --summary-json` (temporary/inspection flag, or a hidden debug path) prints a `RepoSummary` as JSON.
- `.gitignore` and built-in ignores are respected.
- Secrets and large binaries are skipped and noted, never read.
- Languages detected by extension with weights; manifests parsed (at least `package.json`, `pyproject.toml`, `go.mod`).
- Summary is size-bounded (documented caps enforced).
- Not-a-directory and empty-repo produce friendly errors / clearly-empty summary, not crashes.
- Ruff, Black, and pytest pass.

### Manual test checklist
- [x] Run against a Python fixture repo; primary language is Python; `pyproject.toml` appears.
- [x] Run against a Node fixture repo; primary language is JavaScript/TypeScript; `package.json` scripts appear.
- [x] Add a `.gitignore` entry and confirm the matched path is absent from the summary.
- [x] Drop a fake `.env` and a large binary into a fixture; confirm they are skipped and noted.
- [x] Run against a file (not a directory): friendly error, exit 2.
- [x] Run against an empty directory: clearly-empty summary or friendly message, no crash.

### Commits
1. `chore: scaffold package, pyproject, entry point, and tooling config`
2. `feat: add gitignore-aware repo scanner with secret and binary skipping`
3. `feat: detect languages by extension with weights`
4. `feat: parse package.json, pyproject.toml, and go.mod manifests`
5. `feat: build bounded RepoSummary from scan results`
6. `feat: wire click CLI to print RepoSummary as JSON`
7. `test: cover scanner, detection, and summary with fixture repos`

---

## Phase 2: Draft README via Claude API + preview + dry-run

Turn the summary into a drafted README and let the user see it. No write to disk yet; `--dry-run` is effectively the only mode.

### Definition of done
- `api.py` builds a prompt from the summary and calls the Claude API through the `anthropic` SDK.
- API key read from env/`.env`; never logged.
- Returned Markdown is previewed with rich.
- `--model` and `--sections` resolve with documented precedence.
- API errors (network, 429, 401, other) map to distinct friendly messages, exit code 3, no traceback by default.
- Progress spinner during scan and during the API call.
- `--dry-run` prints the draft and writes nothing.
- Tests mock the anthropic client; no network calls in the suite.
- Ruff, Black, and pytest pass.

### Manual test checklist
- [x] With a valid key, `readme-forge . --dry-run` previews a README containing the default sections.
- [x] `--sections "overview,usage,license"` limits the drafted sections.
- [x] `--model some-id` is used (verify via `--verbose` resolved-config output).
- [x] Unset the key: friendly "set ANTHROPIC_API_KEY" message, exit 3, no traceback.
- [x] Simulate network down (no connectivity): friendly network error, exit 3.
- [ ] Simulate 401 (bad key) and 429 (rate limit) via the mock in tests: distinct messages.

### Commits
1. `feat: add Claude API client wrapper and prompt builder`
2. `feat: map anthropic SDK errors to friendly messages and exit codes`
3. `feat: render README preview with rich`
4. `feat: add progress spinners for scan and API call`
5. `feat: resolve model and sections from flags, env, and defaults`
6. `feat: add --dry-run to preview without writing`
7. `test: cover API client and CLI drafting with a mocked client`

---

## Phase 3: Write gate, overwrite safety, and UX polish

Make it write files safely, and finish the CLI UX.

### Definition of done
- Confirm-before-write gate implemented per design.md decision table.
- Existing README never overwritten without `--overwrite` or an explicit "yes".
- Non-interactive stdin with a required confirmation: treated as declined, exit 4, helpful message.
- `--output` controls the write path.
- `--quiet` / `--verbose` behave per design.md.
- `NO_COLOR` and non-TTY disable color; no meaning by color alone.
- Exit codes match design.md across all paths.
- `--help` lists every flag; `--version` works.
- Ruff, Black, and pytest pass.

### Manual test checklist
- [x] New file: `readme-forge .` writes `README.md`, exit 0.
- [ ] Existing file, no flag: prompts, default No; declining writes nothing, exit 0.
- [x] Existing file, `--overwrite`: writes without prompt.
- [x] `--output docs/README.md` writes to that path.
- [x] `NO_COLOR=1 readme-forge .`: no color, still readable.
- [ ] `--quiet` suppresses progress; `--verbose` shows resolved config and skip notes.
- [x] Existing file, no `--overwrite`, piped stdin: exit 4 with guidance.

### Commits
1. `feat: add confirm-before-write gate with overwrite safety`
2. `feat: support --output for custom write path`
3. `feat: honor NO_COLOR and non-TTY for color disabling`
4. `feat: implement --quiet and --verbose output levels`
5. `feat: finalize exit codes and error formatting`
6. `docs: complete help text and usage examples`
7. `test: cover write gate, overwrite, and non-interactive decline`

---

## Phase verification (run after each phase)

- [ ] Build the package (`pip install -e ".[dev]"`) succeeds.
- [ ] `ruff check .` and `black --check .` pass.
- [ ] `pytest` passes with no network access.
- [x] Run the CLI against a real fixture repo and inspect output.
- [x] Unhappy path: path is not a repo/directory -> friendly error, exit 2.
- [x] Unhappy path: empty repo -> clearly-empty summary or friendly message, no crash.
- [x] Unhappy path: existing README without `--overwrite` -> prompts / refuses, never silently overwrites.
- [x] Unhappy path: missing `ANTHROPIC_API_KEY` -> friendly message, exit 3, no traceback.
- [x] Unhappy path: network down -> friendly network error, exit 3.
- [ ] Unhappy path: huge repo -> summary stays under the size cap; run completes in reasonable time.
- [x] Dry-run writes nothing; a normal run writes exactly the target file.
- [ ] `--quiet` and `--verbose` each behave as specified; `NO_COLOR` disables color.

## Backlog

(Empty. Add out-of-scope ideas here with a one-line rationale. Do not implement without promoting to a phase.)
