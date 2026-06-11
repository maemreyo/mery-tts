# Diagnostics event schema bounded retention and sanitization

Status: completed

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Add bounded sanitized diagnostics history covering runtime, install, readiness, synthesis metadata, fallback, cancellation, and errors.

## Acceptance criteria

- [x] Event schema covers startup/shutdown, discovery, provider health, install lifecycle, readiness transitions, smoke, synthesis metadata, fallback, cancellation, and sanitized errors.
- [x] Default retention is 7 days or 1,000 events.
- [x] Corrupt storage does not break synthesis.
- [x] Raw text, tokens, audio, keys, and private paths are redacted.

## Evidence required

- [x] Retention tests.
- [x] Storage corruption test.
- [x] Redaction matrix tests.

## Blocked by

- 01

## Evidence

- `src/mery_tts/schemas/v1.py` and health routes expose distinct live/ready/health semantics.
- `src/mery_tts/diagnostics/history.py` and `src/mery_tts/diagnostics/export.py` implement bounded sanitized diagnostics history and export bundles.
- `tests/contract/test_health_semantics.py`, `tests/contract/test_metrics_opt_in.py`, `tests/unit/test_diagnostics_history.py`, `tests/unit/test_diagnostics_export.py`, and Console/API tests cover the observability contract.
- Verification: ADR-0041 focused verification previously recorded: diagnostics/history gate passed; current API/core verification remains green.
