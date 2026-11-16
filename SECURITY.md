# Security policy

## Supported versions

Only the latest release on `main` receives security fixes.

## Reporting a vulnerability

Please do not open a public issue. Use GitHub's private vulnerability reporting
(Security tab, "Report a vulnerability") or email thealirazadev@gmail.com with the
steps to reproduce. You should get a reply within 72 hours.

## How readme-forge handles sensitive data

- The scanner skips `.env`, `.env.*`, `secrets.*` and other secret-named files, and it honors `.gitignore` (`src/readme_forge/scanner.py`).
- Files above a size limit are never read (`src/readme_forge/scanner.py`).
- An existing README is never overwritten without `--overwrite` or an interactive confirmation, and the confirmation defaults to no (`src/readme_forge/renderer.py`).
- The API key is read from `ANTHROPIC_API_KEY` in the environment or a local `.env` (`src/readme_forge/errors.py`, README).
