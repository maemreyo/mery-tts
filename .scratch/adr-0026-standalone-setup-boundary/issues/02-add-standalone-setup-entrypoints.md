# Add standalone setup entrypoints

Status: completed

## Parent

ADR-0026 — `docs/adr/ADR-0026-standalone-setup-boundary.md`

## What to build

Add Mery-owned setup entrypoints so setup can be started from Console, CLI, or a client handoff without requiring Zam Reader-specific code.

## Acceptance criteria

- [x] Mery exposes a setup console route that accepts setup intent safely.
- [x] CLI can print or open the same setup route for local users.
- [x] Setup entrypoint works when no client identity is provided.
- [x] Setup state is Mery-owned and does not require Zam Reader to remain open.

## Production-ready criteria

- [x] Tests cover console setup route routing, CLI setup URL generation, and client-agnostic setup.
- [x] Security checks prevent arbitrary external redirects or unsafe query values.
- [x] Docs show standalone Mery setup flow independent of Zam Reader.

## Blocked by

- ADR-0026 issue 01-define-setup-intent-contract
