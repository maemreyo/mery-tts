# Create daemon app factory and serve command

Status: production-ready
## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Create daemon/server mode through an app factory and `mery serve`, so the helper can run as a long-lived localhost service with shared dependency construction.

## Acceptance criteria

- [x] The helper exposes an app factory suitable for local development, tests, and `mery serve`.
- [x] `mery serve` starts the daemon using configured host/port settings.
- [x] Startup does not require Zam Reader, real engine packages, or installed models.
- [x] A smoke test proves server construction and shutdown work cleanly.

## Blocked by

- 01-create-cli-entrypoint-and-command-skeleton

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Implement `mery serve` with uvicorn/FastAPI startup, configured host/port, bound-port reporting, signal handling, and clean shutdown.
- [x] Capture real server smoke evidence: start daemon, call `/v1/health`, stop daemon, and verify no process/port is left behind.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Implement `mery serve` with uvicorn/FastAPI startup, configured host/port, bound-port reporting, signal handling, and clean shutdown.
- Capture real server smoke evidence: start daemon, call `/v1/health`, stop daemon, and verify no process/port is left behind.
