# Design decisions

## 1. Send a bounded summary, never the repository

The model never sees source files. `scan_repo` collects paths, extensions, and sizes, and reads
file bodies only for recognized manifests (`package.json`, `pyproject.toml`, `go.mod`, and the
rest of `RECOGNIZED_MANIFESTS`). `build_summary` turns that into a `RepoSummary` and
`_enforce_size_cap` keeps its serialized JSON under `MAX_SUMMARY_BYTES` (20 KB), dropping the
least essential data first: scan notes, then top-level names, entry points, scripts, extra
manifests, and finally languages. Lists and strings have their own caps as well. This keeps the
prompt small and its cost predictable no matter how large the repository is, and it limits what
leaves the machine to structure and manifest fields.

## 2. Filter before reading, not after

Ignore rules are applied during the walk. Built-in directories (`.git`, `node_modules`,
virtualenvs, `dist`, `build`, caches) are pruned from `os.walk` so they are never descended into,
and `.gitignore` is parsed with `pathspec` using gitwildmatch semantics instead of hand-rolled
globbing. Directories are matched with a trailing slash so patterns like `build/` prune whole
subtrees. Secret names (`.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa`, `*.p12`, `credentials`,
`secrets.*`) and anything over 500 KB are rejected on their name and `stat` size alone, so their
contents are never opened. A file that cannot be stat'ed or read is recorded as a note and
skipped; one bad file never aborts the scan.

## 3. Top-level structure comes from scanned files only

The summary's `top_level` list was originally a raw listing of the root directory. That leaked
exactly the names the scanner had filtered out: `node_modules`, `dist`, `build`, `.env`, and
skipped binaries all reached the prompt. `_detect_top_level` now derives the list from the first
path component of files that survived the scan, and a test asserts that ignored, secret, and
oversized paths never appear there.

## 4. Same tree in, same summary out

The walk sorts directory and file names, languages are sorted by weight then name, manifests by
path, and `to_json` uses `sort_keys=True`. A deterministic summary makes the prompt reproducible,
makes tests stable, and means two runs on an unchanged repository send the same request.

## 5. Parse a few manifests well

Only `package.json`, `pyproject.toml`, and `go.mod` have parsers. Other recognized manifests are
still counted as files and influence language detection, but their fields are not extracted. A
malformed manifest (bad JSON or TOML) is skipped with a note rather than failing the run. TOML is
read with the stdlib `tomllib` on Python 3.11+ and the `tomli` backport on 3.10, which is pinned
with an environment marker so 3.11+ installs do not pull it in.

## 6. The write gate is a pure decision function

`decide_write_action(exists, overwrite, dry_run)` returns `WRITE`, `PROMPT`, or `SKIP`, and the
CLI acts on the result. Keeping the decision separate from I/O makes every row of the table
testable without a terminal. `--dry-run` wins over `--overwrite`. An existing file without
`--overwrite` prompts with a default of No, and declining exits 0 having written nothing. When a
prompt is needed but stdin is not a TTY, the CLI refuses with exit code 4 and tells the user to
pass `--overwrite` instead of hanging on input that will never arrive. A consequence is that
piping `n` into the prompt also exits 4, because piped stdin is never interactive; the
interactive decline path is covered by tests.

## 7. Create the output directory on write

`--output docs/README.md` into a folder that did not exist used to fail with an `OSError` and
exit 1. The CLI now calls `mkdir(parents=True, exist_ok=True)` on the output's parent right
before writing, after the write gate has approved the write, so a refused or dry run still
creates nothing.

## 8. Typed errors map to exit codes and one-line messages

Every expected failure is a `ReadmeForgeError` subclass carrying its own `exit_code`: 2 for usage
errors and non-directory paths, 3 for API errors, 4 for a refused overwrite, 1 for write
failures. Anthropic SDK exceptions are translated by `map_anthropic_error` so an invalid key
(401), a rate limit (429), a connection or timeout failure, and other HTTP errors each produce a
distinct actionable message. A last-resort `except Exception` around the whole run turns a
genuine bug into exit 1 with a friendly line. Tracebacks are printed only with `--verbose`.

## 9. Key handling and ordering of checks

The API key is read from `ANTHROPIC_API_KEY`, with `.env` loaded through `python-dotenv`, and
there is no fallback value. It is passed straight to the SDK client and never printed. The key is
looked up only after scanning, so `--summary-json` and the empty-repository path (which exits 0
with a message instead of calling the API with nothing useful) work without a key. The model id
resolves as `--model`, then `README_FORGE_MODEL`, then the built-in default.

## 10. Logging is scoped to the package logger

`configure_logging` sets the level on the `readme_forge` logger only and disables propagation.
An earlier version used `logging.basicConfig`, which configures the root logger; under
`--verbose` that switched on DEBUG output from third-party libraries (markdown-it internals)
and buried the tool's own messages. User-facing output goes through rich consoles and is kept
separate from logs.

## 11. Color is optional and never carries meaning alone

`resolve_color` disables color whenever `NO_COLOR` is set to any value, and otherwise enables it
only when stdout is a TTY, so redirected output contains no ANSI codes. Errors are printed through
a dedicated stderr rich `Console`, which gives the red `Error:` prefix under color and the plain
prefix without it, with no hand-written escape codes. Every state also has a text form:
`Error:`, `OK:`, `(exists)`, `(new file)`.

## 12. Reproducible installs

Runtime and dev dependencies are pinned with `==` in `pyproject.toml`, and `requirements.lock`
pins the full transitive set. CI installs the lockfile first and then the package with its dev
extras, on Python 3.10 and 3.12, so the lowest supported version is always exercised. Coverage
is part of every `pytest` run through `addopts`, with `fail_under = 90` in the coverage config.
