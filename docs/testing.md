# Testing: readme-forge

## Strategy

- **pytest** is the test runner. The Anthropic API is **always mocked**; the suite must never make a network call. Enforce this by injecting a fake client (or monkeypatching the `anthropic` client factory) so a real key is never needed to run tests.
- **Fixture repos** live under `tests/fixtures/` (for example `python_repo/`, `node_repo/`, `go_repo/`, `empty_repo/`, `mixed_repo/`). Tests point the scanner at these directories and assert on the resulting `RepoSummary`.
- **Unit tests** cover pure logic:
  - `test_scanner.py`: ignore rules (`.gitignore` + built-ins), secret/binary skipping, unreadable-file handling, size caps.
  - `test_detect.py`: language weighting, manifest parsing (JSON/TOML/YAML) including malformed manifests.
  - `test_summary.py`: summary assembly, determinism (same tree -> same summary), size-bound enforcement.
  - `test_api.py`: prompt building from a summary; error mapping for network / 429 / 401 / other, using a mocked client that raises the corresponding SDK exceptions.
  - `test_renderer.py`: preview rendering, `NO_COLOR`/non-TTY color disabling, confirm-before-write decision logic.
  - `test_cli.py`: end-to-end via click's `CliRunner` with the client mocked. Covers happy path plus unhappy paths (not a directory, empty repo, existing README without `--overwrite`, missing key, simulated API errors, `--dry-run` vs write, `--quiet` vs `--verbose`).
- **Manual QA** (not automated) covers real API behavior and terminal appearance: run the CLI against a real repo with a real key, confirm the preview looks right, color on/off, progress indicators, and that the write gate behaves interactively. See `phases.md` manual checklists.

## What to assert

- Scanner never yields a path matched by ignore rules, a secret file, or a file over the size cap.
- The summary serialized size stays under the documented cap for a large synthetic tree.
- Each API error type produces the expected exit code (3) and a message that does not contain a traceback (unless `--verbose`).
- The write gate never overwrites an existing file without `--overwrite` or a "yes" confirmation.
- The API key never appears in captured stdout, stderr, or log output.

## Exact commands

Install (with dev extras):

```
pip install -e ".[dev]"
```

Lint:

```
ruff check .
```

Format check:

```
black --check .
```

Tests:

```
pytest
```

Tests with coverage (optional, for local inspection):

```
pytest --cov=readme_forge --cov-report=term-missing
```

Build the distribution:

```
python -m build
```

## Gate

A feature is not "done" until, on a clean checkout of that commit:

- `pip install -e ".[dev]"` succeeds,
- `ruff check .` passes,
- `black --check .` passes,
- `pytest` passes with no network access.

The build (`python -m build`) and the full test suite must pass before a feature is considered complete and before publishing.
