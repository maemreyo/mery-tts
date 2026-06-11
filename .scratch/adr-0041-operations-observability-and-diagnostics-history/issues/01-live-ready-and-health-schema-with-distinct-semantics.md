# Live ready and health schema with distinct semantics

Status: completed

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Separate live, ready, and health states so clients can distinguish process liveness from synthesis readiness and subsystem degradation.

## Acceptance criteria

- [x] Live means process alive.
- [x] Ready means at least one usable voice can synthesize.
- [x] Health includes subsystem diagnostics and degradation.
- [x] Tests cover live-but-not-ready, ready, degraded, and unavailable states.

## Evidence required

- [x] Endpoint/schema contract tests.
- [x] Fake subsystem tests for all states.
- [x] API docs excerpt.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/schemas/v1.py` and health routes expose distinct live/ready/health semantics.
- `src/mery_tts/diagnostics/history.py` and `src/mery_tts/diagnostics/export.py` implement bounded sanitized diagnostics history and export bundles.
- `tests/contract/test_health_semantics.py`, `tests/contract/test_metrics_opt_in.py`, `tests/unit/test_diagnostics_history.py`, `tests/unit/test_diagnostics_export.py`, and Console/API tests cover the observability contract.
- Verification: ADR-0041 focused verification previously recorded: diagnostics/history gate passed; current API/core verification remains green.
