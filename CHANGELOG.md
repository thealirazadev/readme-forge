# Changelog

## Unreleased

### Added
- Exit codes and error formatting, plus complete help text and usage examples.
- `--quiet` and `--verbose` output levels, and color is disabled by `NO_COLOR` and when output is
  not a terminal.
- Pinned lockfile for reproducible installs.
- CI runs lint, the format check, and tests on every push and pull request, with a 90 percent
  coverage gate.

### Fixed
- `--output` creates missing parent directories.
- The summary lists only scanned top-level paths, so ignored paths never reach the prompt.
- Upgraded black, setuptools, and wheel to resolve security advisories.

## 0.1.0

Scans a repository, drafts a `README.md` with the Claude API, and shows a preview that you
confirm before anything is written, with `--output`, `--overwrite`, `--dry-run`, and `--sections`.
