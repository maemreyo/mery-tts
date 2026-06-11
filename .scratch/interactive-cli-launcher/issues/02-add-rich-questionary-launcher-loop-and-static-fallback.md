# Add Rich/questionary launcher loop and static fallback

Status: completed
Type: AFK

## What to build

Add the human interactive frontend for `mery launch`: Rich-rendered landing/menu surfaces, optional `questionary` selection through a narrow prompt adapter, persistent loop behavior, and safe static fallback when there is no TTY or the optional interactive dependency is unavailable.

## Acceptance criteria

- [x] `mery launch` in a TTY renders a polished, grouped menu using Rich plus the optional prompt adapter.
- [x] Missing optional interactive dependency prints clear install guidance and exits 0 instead of crashing.
- [x] Non-TTY stdin/stdout prints static command guidance and exits 0 instead of blocking.
- [x] Launcher returns to the menu by default after non-blocking actions.
- [x] Ctrl+C/cancel exits cleanly without traceback.
- [x] Prompt integration is isolated behind an adapter that can be faked in tests.
- [x] Tests cover missing dependency fallback, non-TTY fallback, cancel behavior, and loop dispatch using a fake prompt.

## Evidence

- `src/mery_tts/cli/launcher/prompts.py`
- `src/mery_tts/cli/launcher/render.py`
- `tests/cli/test_launch.py`

## Blocked by

- `01-add-launcher-action-registry-and-automation-surface.md`
