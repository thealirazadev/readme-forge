# Changelog

## Unreleased

### Added
- Exit codes and error formatting, plus complete help text and usage examples.
- `--quiet` and `--verbose` output levels, and color is disabled by `NO_COLOR` and when output is
  not a terminal.
- Pinned lockfile for reproducible installs.
- CI runs lint, the format check, and tests on every push and pull request, with a 90 percent
  coverage gate.
- Fields are extracted from `Cargo.toml`, `composer.json`, `pubspec.yaml`, and `Gemfile`, as
  the README already listed.

### Fixed
- A `.env` in the working directory is now found when the tool is installed (it was searched
  for relative to the installed package).
- CircleCI (`.circleci/`) is detected as CI.
- A manifest whose top level is not an object, or whose fields have the wrong type, is skipped
  or trimmed instead of aborting the run.
- `--output` creates missing parent directories.
- The summary lists only scanned top-level paths, so ignored paths never reach the prompt.
- Upgraded black, setuptools, and wheel to resolve security advisories.

## 0.1.0

Scans a repository, drafts a `README.md` with the Claude API, and shows a preview that you
confirm before anything is written, with `--output`, `--overwrite`, `--dry-run`, and `--sections`.
