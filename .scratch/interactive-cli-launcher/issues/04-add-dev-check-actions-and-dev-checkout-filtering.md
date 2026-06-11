# Add dev-check actions and dev-checkout filtering

Status: completed
Type: AFK

## What to build

Add developer-only launcher actions for verification gates such as `make check` and `pnpm console-check`, visible only when running from a repository checkout. Dev actions should use an injectable subprocess runner, stream useful output for humans, and provide structured results for JSON mode.

## Acceptance criteria

- [x] Launcher context detects dev checkout mode using repo-local markers such as `Makefile`, `pyproject.toml`, and `web/console/package.json`.
- [x] Dev actions are hidden from interactive and `--list-actions` output outside dev checkout mode.
- [x] `python-check` runs the canonical Python gate from the repo root through the runner abstraction.
- [x] `console-check` runs the canonical Console gate from `web/console` through the runner abstraction.
- [x] Long-running/dev actions require explicit confirmation in interactive mode or a safe non-interactive flag when applicable.
- [x] JSON results include command, cwd, exit code, and summarized status without embedding excessive logs.
- [x] Tests cover dev/non-dev filtering and runner success/failure without invoking real `make` or `pnpm`.

## Evidence

- `src/mery_tts/cli/launcher/context.py`
- `src/mery_tts/cli/launcher/runner.py`
- `src/mery_tts/cli/launcher/actions.py`
- `tests/cli/test_launch.py`

## Blocked by

- `01-add-launcher-action-registry-and-automation-surface.md`
- `02-add-rich-questionary-launcher-loop-and-static-fallback.md`
