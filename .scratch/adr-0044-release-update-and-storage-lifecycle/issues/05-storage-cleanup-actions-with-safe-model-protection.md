# Storage cleanup actions with safe model protection

Status: completed

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Expose cleanup actions for caches, logs, and diagnostics while protecting active models and voices from auto-deletion.

## Acceptance criteria

- [x] Cleanup actions exist for caches, logs, and diagnostics.
- [x] Models/voices in active use are protected.
- [x] CLI and Console expose cleanup commands/actions.
- [x] Eviction is safe and auditable.

## Evidence required

- [x] Cleanup tests.
- [x] Active model protection tests.
- [x] CLI/Console proof.
- [x] Audit/diagnostics evidence.

## Blocked by

- 04

## Evidence

- `src/mery_tts/schemas/v1.py`, catalog refresh/install/verifier modules, storage identity code, and API routes implement layered versioning, catalog rollback, explicit confirmation, storage measurement, and safe cleanup.
- Console assets expose confirmation, storage advisory, and safe cleanup actions while refusing model cleanup.
- `tests/unit/test_catalog_refresh_install.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, `tests/unit/test_storage_identity.py`, and `tests/contract/test_api_core.py` cover release/update/storage lifecycle behavior.
- Verification: ADR-0044 focused verification previously recorded: release/update/storage lifecycle gate passed; current API/core verification remains green.
