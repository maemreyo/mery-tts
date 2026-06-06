# Create CLI entrypoint and command skeleton

Status: scaffold-complete; runtime-follow-up

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

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Replace placeholder command output for `serve`, `engines`, `voices`, `catalog`, `models`, and `speak` with calls into shared runtime services.
- [ ] Add CLI subprocess smoke tests for successful commands and failure exit codes using an isolated runtime directory.

## Comments
