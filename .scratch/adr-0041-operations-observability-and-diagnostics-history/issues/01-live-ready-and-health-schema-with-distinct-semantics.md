# Live ready and health schema with distinct semantics

Status: needs-triage

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Separate live, ready, and health states so clients can distinguish process liveness from synthesis readiness and subsystem degradation.

## Acceptance criteria

- [ ] Live means process alive.
- [ ] Ready means at least one usable voice can synthesize.
- [ ] Health includes subsystem diagnostics and degradation.
- [ ] Tests cover live-but-not-ready, ready, degraded, and unavailable states.

## Evidence required

- [ ] Endpoint/schema contract tests.
- [ ] Fake subsystem tests for all states.
- [ ] API docs excerpt.

## Blocked by

None - can start immediately
