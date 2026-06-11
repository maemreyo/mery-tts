# CLI and console diagnostics history UX

Status: completed

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Add user-facing diagnostics history, retention status, export, deletion, and recovery guidance surfaces.

## Acceptance criteria

- [x] User Mode shows actionable readiness/recovery.
- [x] Developer Mode shows diagnostics history and debug metadata.
- [x] Retention status and delete-history action are visible.
- [x] CLI exposes equivalent diagnostics commands.

## Evidence required

- [x] Console UI tests.
- [x] CLI command tests.
- [x] Evidence for retention status and delete action.

## Blocked by

- 02

## Evidence

- `src/mery_tts/schemas/v1.py` and health routes expose distinct live/ready/health semantics.
- `src/mery_tts/diagnostics/history.py` and `src/mery_tts/diagnostics/export.py` implement bounded sanitized diagnostics history and export bundles.
- `tests/contract/test_health_semantics.py`, `tests/contract/test_metrics_opt_in.py`, `tests/unit/test_diagnostics_history.py`, `tests/unit/test_diagnostics_export.py`, and Console/API tests cover the observability contract.
- Verification: ADR-0041 focused verification previously recorded: diagnostics/history gate passed; current API/core verification remains green.
