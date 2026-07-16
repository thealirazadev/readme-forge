# Launch checklist: readme-forge

Check every item before publishing. Nothing ships with an unchecked box.

## Correctness and safety

- [x] Dependency versions pinned with `==` in `pyproject.toml`; lockfile committed.
- [x] Console entry point `readme-forge` works after a clean install (`pipx install .` / `pip install .`).
- [x] Tool never overwrites an existing README without `--overwrite` or an explicit confirmation.
- [x] `--dry-run` writes nothing under all flag combinations.
- [x] All model API errors handled (network, rate limit 429, invalid key 401, other) with friendly messages and exit code 3; no raw traceback unless `--verbose`.
- [x] Not-a-directory path -> friendly error, exit 2.
- [x] Empty repo -> clearly-empty summary or friendly message, no crash.
- [x] API key read only from env/`.env`; never hardcoded, never logged.
- [x] `.gitignore` respected; secrets and large binaries skipped and never sent to the API.

## UX and accessibility

- [x] `NO_COLOR` respected; non-TTY output has no ANSI codes.
- [x] No meaning conveyed by color alone (text/ASCII prefixes for error/warning/success/status).
- [x] `--quiet` and `--verbose` behave per design.md and are mutually exclusive.
- [x] Help text complete: `readme-forge --help` lists every flag with a one-line description.
- [x] `--version` prints the version and exits 0.
- [x] Progress shown while scanning and while calling the API (suppressed under `--quiet`).
- [x] Preview shown before any write; target path and existence stated.
- [x] Exit codes match design.md across all paths.

## Quality gates

- [x] `ruff check .` passes.
- [x] `black --check .` passes.
- [x] `pytest` passes with no network access (API mocked).
- [x] `python -m build` succeeds; wheel and sdist produced.
- [x] README install/usage/test steps verified against a clean environment.
- [x] No emoji and no authorship attribution anywhere in code, docs, or commits.
- [x] Commit history follows Conventional Commits, one commit per feature.

## PyPI publish

- [x] `pyproject.toml` metadata complete: name, version, description, authors, license (MIT), Python requirement, classifiers, project URLs.
- [x] `LICENSE` file present (MIT) and referenced.
- [x] Long description (README) renders correctly on PyPI (`twine check dist/*`).
- [ ] Version number bumped and tagged for the release.
- [ ] Uploaded to TestPyPI first and installed from there in a clean venv; entry point works.
- [ ] Uploaded to PyPI (`twine upload dist/*`); install from PyPI verified.
- [x] `.env.example` present and using dummy values only; real `.env` not packaged or committed.
