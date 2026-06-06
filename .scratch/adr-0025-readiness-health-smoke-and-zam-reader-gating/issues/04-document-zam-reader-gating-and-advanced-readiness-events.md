# Document Zam Reader gating and advanced readiness events

Status: ready-for-human

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Document how Zam Reader should interpret unavailable, degraded, and ready Mery states, and document deferred advanced readiness events for future WebSocket streaming.

## Acceptance criteria

- [ ] Docs define unavailable, degraded, and ready states in terms Zam Reader can display.
- [ ] Docs state Web Speech fallback remains available whenever Mery is unavailable or degraded.
- [ ] Docs describe that ready requires paired/authenticated helper, contract compatibility, Piper and Kokoro installed, deep smoke passed, and fallback verified.
- [ ] Deferred readiness events over `/v1/events` are listed as future work.

## Production-ready criteria

- [ ] Human review confirms gating language matches product UX expectations.
- [ ] Docs cross-link ADR-0021, ADR-0025, and the Zam Reader readiness contract.
- [ ] Future event work has explicit acceptance criteria and is not implied as first-milestone complete.

## Blocked by

- ADR-0025 issue 01-expand-health-to-layered-readiness-contract
