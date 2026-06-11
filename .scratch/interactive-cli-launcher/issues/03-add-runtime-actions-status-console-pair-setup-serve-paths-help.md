# Add runtime launcher actions for status, Console, pairing, setup, serve, paths, and help

Status: completed
Type: AFK

## What to build

Add the first production runtime actions to the launcher using direct Python service calls where possible: layered status summary, open Web Console, foreground server start, pair client, show setup URL, show API/OpenAPI URLs, show storage/config paths, and list/open local help topics.

## Acceptance criteria

- [x] `status` returns a shallow layered summary covering server reachability, Console URL, auth/token configured state without secrets, engine summary, installed voice count, storage signal, and last doctor signal when available.
- [x] `open-console` opens the configured local Console URL only when explicitly selected or run via `--action`; tests fake the browser opener.
- [x] `serve-foreground` clearly explains that logs attach to the current terminal and Ctrl+C stops the server; managed background serving remains out of scope.
- [x] `pair` creates a pairing challenge without printing long-lived tokens.
- [x] `setup-url` renders the local setup URL using existing setup conventions.
- [x] `api-docs` / `openapi` actions show or open the localhost docs/OpenAPI URLs based on configured port.
- [x] `paths` shows storage/config/log/diagnostics paths in a user-friendly way without leaking private contents.
- [x] `help` lists packaged local help topics and can show a selected topic.
- [x] Tests use temp runtime paths and fakes/mocks for browser, server, and stores; no optional engine or network is required.

## Evidence

- `src/mery_tts/cli/launcher/services.py`
- `src/mery_tts/cli/launcher/actions.py`
- `tests/cli/test_launch.py`

## Blocked by

- `01-add-launcher-action-registry-and-automation-surface.md`
- `02-add-rich-questionary-launcher-loop-and-static-fallback.md`
