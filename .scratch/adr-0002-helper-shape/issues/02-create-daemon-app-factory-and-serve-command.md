# Create daemon app factory and serve command

Status: ready-for-agent

## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Create daemon/server mode through an app factory and `mery serve`, so the helper can run as a long-lived localhost service with shared dependency construction.

## Acceptance criteria

- [ ] The helper exposes an app factory suitable for local development, tests, and `mery serve`.
- [ ] `mery serve` starts the daemon using configured host/port settings.
- [ ] Startup does not require Zam Reader, real engine packages, or installed models.
- [ ] A smoke test proves server construction and shutdown work cleanly.

## Blocked by

- 01-create-cli-entrypoint-and-command-skeleton

## Comments
