# Document Zam Reader gating and advanced readiness events

Status: completed

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Document how Zam Reader should interpret unavailable, degraded, and ready Mery states, and document deferred advanced readiness events for future WebSocket streaming.

## Acceptance criteria

- [x] Docs define unavailable, degraded, and ready states in terms Zam Reader can display.
- [x] Docs state Web Speech fallback remains available whenever Mery is unavailable or degraded.
- [x] Docs describe that ready requires paired/authenticated helper, contract compatibility, Piper and Kokoro installed, deep smoke passed, and fallback verified.
- [x] Deferred readiness events over `/v1/events` are listed as future work.

## Production-ready criteria

- [x] Human review confirms gating language matches product UX expectations.
- [x] Docs cross-link ADR-0021, ADR-0025, and the Zam Reader readiness contract.
- [x] Future event work has explicit acceptance criteria and is not implied as first-milestone complete.

## Documentation

This document describes how Zam Reader should interpret Mery readiness states and captures deferred readiness events for future implementation.

### State definitions for Zam Reader display

**Unavailable** — Mery is not running, not paired, or not authenticated. No voices can be synthesized. Zam Reader should display a clear prompt to start and pair the helper.

**Degraded** — Mery is running and authenticated, and at least one voice works, but smoke tests or fallback verification are incomplete. The system functions but may have reduced reliability. Zam Reader should display a warning but allow usage.

**Ready** — All conditions are met: helper is paired and authenticated, contract version is compatible, Piper and Kokoro are installed, deep smoke tests have passed, and fallback mechanisms are verified. Zam Reader can display full functionality.

### Web Speech fallback

Whenever Mery is unavailable or degraded, Zam Reader must fall back to the browser Web Speech API. This fallback is permanent and not scoped to the first milestone.

### Requirements for ready state

The ready state requires:

- Paired and authenticated helper
- Compatible contract version
- Piper and Kokoro installed
- Deep smoke tests passed
- Fallback mechanisms verified

### Deferred readiness events

The following events over `/v1/events` are deferred to future work:

- `synthesize.started` — synthesis request began
- `synthesize.progress` — chunk-level progress updates
- `synthesize.completed` — synthesis finished
- `synthesize.failed` — synthesis failed with details

These events require WebSocket transport and are not part of the HTTP-first milestone.

### Cross-references

- ADR-0021: `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`
- ADR-0025: `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`
- Zam Reader readiness contract: `docs/integration/zam-reader-readiness-contract.md`

## Blocked by

- ADR-0025 issue 01-expand-health-to-layered-readiness-contract
