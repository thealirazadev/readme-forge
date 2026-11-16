# Security policy

## Supported versions

Only the latest release (0.1.0, the version in `pyproject.toml`) on `main` receives security
fixes.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private vulnerability reporting
(Security tab, "Report a vulnerability") or email thealirazadev@gmail.com with the
steps to reproduce. You should get a reply within 72 hours.

## How readme-forge protects your code and key

- The Anthropic API key is read from `ANTHROPIC_API_KEY` (or a local `.env`) and is not written
  to the output.
- Files matching secret patterns (`.env`, `*.pem`, `id_rsa`, `secrets.*`, and similar) are
  skipped during the scan.
- Ignored paths from `.gitignore` and large binaries are left out of the summary sent to the
  model.
- A structured summary of the repository is sent to the Claude API to draft the README, so do
  not run it on private code you are not allowed to share with that service.
- The draft is shown as a preview. Nothing is written to disk without confirmation, and an
  existing README is replaced only with `--overwrite`.
