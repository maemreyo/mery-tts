# Sanitized diagnostics export bundle

Status: completed

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Expose a sanitized diagnostics export bundle through backend service, CLI, and console trigger/download.

## Acceptance criteria

- [x] Bundle includes versions, platform, engine/provider health, installed voice summary, catalog summary, install states, readiness/smoke status, recent diagnostics, and audit summary.
- [x] Bundle excludes raw input text, tokens, API keys, reference audio, model binaries, and unsanitized private paths.
- [x] CLI and backend expose same behavior.
- [x] Console can trigger/download export.

## Evidence required

- [x] Export bundle contract test.
- [x] Redaction tests.
- [x] CLI/API/Console proof.

## Blocked by

- 02

## Evidence

- `src/mery_tts/schemas/v1.py` and health routes expose distinct live/ready/health semantics.
- `src/mery_tts/diagnostics/history.py` and `src/mery_tts/diagnostics/export.py` implement bounded sanitized diagnostics history and export bundles.
- `tests/contract/test_health_semantics.py`, `tests/contract/test_metrics_opt_in.py`, `tests/unit/test_diagnostics_history.py`, `tests/unit/test_diagnostics_export.py`, and Console/API tests cover the observability contract.
- Verification: ADR-0041 focused verification previously recorded: diagnostics/history gate passed; current API/core verification remains green.
