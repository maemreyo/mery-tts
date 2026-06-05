# Create CLI entrypoint and command skeleton

Status: ready-for-agent

## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Create the `mery` CLI root and command skeletons needed for standalone support and diagnostics, wiring commands to shared service interfaces rather than browser or API internals.

## Acceptance criteria

- [ ] `mery --version`, `doctor`, `serve`, `pair`, `engines`, `voices`, `catalog`, `models`, `storage`, and `speak` commands exist.
- [ ] CLI commands return deterministic exit codes and structured output suitable for tests.
- [ ] Commands delegate to shared helper services instead of duplicating domain logic.
- [ ] CLI tests cover command registration and basic help/version output.

## Blocked by

- ADR-0001 issue 01-create-standalone-helper-package-boundary

## Comments
