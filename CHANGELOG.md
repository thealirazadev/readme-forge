# Changelog

## Unreleased

### Added
- Continuous integration enforces at least 90 percent test coverage.
- Exit codes are finalized, and errors are formatted consistently.
- `--quiet` and `--verbose` set the output level.
- `NO_COLOR` and non-terminal output disable color.
- `--output` sets a custom path for the written README.
- A confirm-before-write gate protects existing files.
- `--dry-run` previews the README without writing it.
- The model and sections are resolved from flags, environment and defaults.
- Progress spinners show during the scan and the API call.
- The README preview is rendered with rich.
- Anthropic SDK errors map to friendly messages and exit codes.
- The Claude API client and prompt builder were added.
- The click CLI prints the repo summary as JSON.
- A bounded repo summary is built from the scan results.
- `package.json`, `pyproject.toml` and `go.mod` manifests are parsed.
- Languages are detected by file extension, with weights.
- A gitignore-aware scanner skips secrets and binary files.

### Fixed
- `--output` creates missing parent directories.
- The summary lists only scanned top-level paths, so ignored paths never reach the prompt.
- Black, setuptools and wheel were upgraded to patch security advisories.
- The gitignore matcher uses the non-deprecated pathspec factory.
