# Optional Prometheus metrics opt-in path

Status: completed

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Document and gate optional Prometheus-compatible local metrics for on-prem operators.

## Acceptance criteria

- [x] Metrics are local-only and opt-in.
- [x] No outbound telemetry is enabled by default.
- [x] Docs list metric categories and privacy boundaries.
- [x] Tests prove disabled-by-default and opt-in behavior.

## Evidence required

- [x] Docs excerpt.
- [x] Config tests for disabled/enabled states.
- [x] No outbound telemetry assertion.

## Blocked by

- 03

## Evidence

- `src/mery_tts/schemas/v1.py` and health routes expose distinct live/ready/health semantics.
- `src/mery_tts/diagnostics/history.py` and `src/mery_tts/diagnostics/export.py` implement bounded sanitized diagnostics history and export bundles.
- `tests/contract/test_health_semantics.py`, `tests/contract/test_metrics_opt_in.py`, `tests/unit/test_diagnostics_history.py`, `tests/unit/test_diagnostics_export.py`, and Console/API tests cover the observability contract.
- Verification: ADR-0041 focused verification previously recorded: diagnostics/history gate passed; current API/core verification remains green.
