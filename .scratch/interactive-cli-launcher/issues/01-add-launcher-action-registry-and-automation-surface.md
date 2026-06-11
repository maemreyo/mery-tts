# Add launcher action registry and automation surface

Status: completed
Type: AFK

## What to build

Create the first vertical slice of the `mery launch` architecture: a modular launcher package with an action registry, launcher context, structured action results, stable action IDs, `--list-actions`, `--action <id>`, and `--json` output. This slice should be usable without a real interactive terminal and without optional prompt dependencies.

## Acceptance criteria

- [x] `mery launch --list-actions` lists stable action IDs grouped for Quick actions, Developer tools, and Help.
- [x] `mery launch --list-actions --json` emits structured JSON that tests can assert without Rich-output parsing.
- [x] `mery launch --action <id>` dispatches through the same registry used by the future interactive menu.
- [x] Action handlers return a structured result object with status, title, message, and data.
- [x] Dev-only actions are modeled in metadata even if their handlers arrive in a later slice.
- [x] Invalid action IDs return a user-friendly error and a non-zero CLI exit code.
- [x] Existing `mery`, `mery --help`, and current subcommands remain scriptable and unchanged.
- [x] Unit/CLI tests cover action registry filtering, JSON serialization, invalid action handling, and non-interactive dispatch.

## Evidence

- `src/mery_tts/cli/launcher/types.py`
- `src/mery_tts/cli/launcher/actions.py`
- `src/mery_tts/cli/launcher/app.py`
- `tests/cli/test_launch.py`

## Blocked by

None - can start immediately.
