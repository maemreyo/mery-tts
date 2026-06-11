# Storage measurement and advisory UI

Status: completed

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Measure models, cache, logs, and diagnostics storage with thresholds and advisory warnings in doctor/console.

## Acceptance criteria

- [x] Doctor/Console show storage breakdown by category.
- [x] Threshold warnings are configurable.
- [x] Measurement handles empty, partial, and full install states.
- [x] Advisory UI is informational before destructive actions.

## Evidence required

- [x] Storage measurement tests.
- [x] Doctor/Console UI proof.
- [x] Threshold config tests.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/schemas/v1.py`, catalog refresh/install/verifier modules, storage identity code, and API routes implement layered versioning, catalog rollback, explicit confirmation, storage measurement, and safe cleanup.
- Console assets expose confirmation, storage advisory, and safe cleanup actions while refusing model cleanup.
- `tests/unit/test_catalog_refresh_install.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, `tests/unit/test_storage_identity.py`, and `tests/contract/test_api_core.py` cover release/update/storage lifecycle behavior.
- Verification: ADR-0044 focused verification previously recorded: release/update/storage lifecycle gate passed; current API/core verification remains green.
