# Design: readme-forge CLI UX

This document specifies the command-line user experience: flags, output, progress, preview, the write gate, exit codes, verbosity, and accessibility.

## Command shape

```
readme-forge [OPTIONS] PATH
```

- `PATH` — positional, the repository directory to scan. Defaults to `.` if omitted.

## Flags

| Flag | Type | Default | Behavior |
| --- | --- | --- | --- |
| `--output PATH` | path | `<PATH>/README.md` | Where to write the generated README. |
| `--overwrite` | bool | off | Allow replacing an existing file at the output path (still previews; skips the confirmation prompt for existing files). |
| `--dry-run` | bool | off | Scan, draft, and preview, but write nothing. Overrides `--overwrite` for writing. |
| `--model TEXT` | str | resolved default | Claude model id. Precedence: `--model` > `README_FORGE_MODEL` > built-in default. |
| `--sections TEXT` | str (csv) | default set | Comma-separated section list to include, e.g. `overview,install,usage,license`. |
| `--quiet` | bool | off | Minimal output: no progress, only the preview (or nothing with `--dry-run`+pipe) and errors. |
| `--verbose` | bool | off | Detailed output: scan decisions, skipped files, API detail, tracebacks on error. |
| `--version` | bool | off | Print version and exit 0. |
| `--help` | bool | off | Print full help with every flag and exit 0. |

`--quiet` and `--verbose` are mutually exclusive; passing both is a usage error (exit 2).

## Output and progress

- Uses a single rich `Console`. Color is enabled only when stdout is a TTY and `NO_COLOR` is unset.
- **Scanning:** show a progress indicator (spinner + current step: "Scanning files...", "Detecting languages...", "Parsing manifests..."). Under `--quiet`, no progress is shown.
- **Calling the API:** show a spinner "Drafting README with Claude..." during the request. Under `--quiet`, no spinner.
- **Detected summary (non-quiet):** a short, human-readable recap before drafting, for example: primary language, number of files, manifests found, whether tests/CI were detected. Rendered as a small table.

## Preview

- After drafting, render the README with rich's Markdown renderer inside a bordered panel titled with the target path and whether it exists.
- Above the preview, print a one-line status: `Target: /path/README.md (exists)` or `(new file)`.
- Under `--quiet`, the preview panel border/title may be omitted but the draft content is still shown (unless `--dry-run` is piped, where the raw Markdown is printed to stdout for redirection).
- Under `--dry-run`, print the draft and stop; state clearly "Dry run: nothing written."

## Confirm-before-write (the write gate)

Decision table:

| Output exists? | `--overwrite`? | `--dry-run`? | Action |
| --- | --- | --- | --- |
| no | any | no | Write directly after preview (no prompt needed for a new file; optional "Write to X? [Y/n]"). |
| yes | no | no | Prompt: `README.md already exists. Overwrite? [y/N]`. Default No. Declining writes nothing, exit 0. |
| yes | yes | no | Write after preview, no prompt. |
| any | any | yes | Never write. Print "Dry run: nothing written." Exit 0. |

- The confirmation prompt defaults to No for existing files (capital N).
- When stdin is not a TTY and a confirmation would be required, do not hang: treat as declined and print a message telling the user to pass `--overwrite`. Exit 4.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success (wrote the file), or user cleanly declined, or `--dry-run`, or `--help`/`--version`. |
| 1 | Unexpected runtime error (I/O, parsing bug). |
| 2 | Usage error (bad flags, path not a directory, conflicting flags). |
| 3 | Model API error (network, rate limit, invalid key, other HTTP). |
| 4 | Write refused because output exists and cannot proceed non-interactively without `--overwrite`. |

## Verbosity levels

- **Default:** progress + summary recap + preview + write gate. One-line friendly errors.
- **`--quiet`:** suppress progress and recap; keep preview content and errors. Logging at ERROR.
- **`--verbose`:** add skipped-file notes, resolved config (model, sections, output path), API request detail (status, request id), and full tracebacks on failure. Logging at DEBUG.

## Accessibility

- **`NO_COLOR` respected:** if set (any value) or stdout is not a TTY, disable all ANSI color and styling.
- **No meaning by color alone:** every state that uses color also uses text/symbols. Errors are prefixed with `Error:`, warnings with `Warning:`, success with `OK:` (ASCII, not emoji). Status like "(exists)" / "(new file)" is text, not a colored dot.
- Tables and panels degrade to plain ASCII when color/box drawing is unavailable.
- No reliance on Unicode-only glyphs for essential meaning; keep symbols ASCII where they carry information.
