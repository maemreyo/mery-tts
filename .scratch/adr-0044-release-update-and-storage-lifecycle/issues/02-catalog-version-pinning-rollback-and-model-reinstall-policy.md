# Catalog version pinning rollback and model reinstall policy

Status: completed

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Pin catalog versions, rollback to previous valid catalog, and handle corrupt model artifacts by reinstalling same version.

## Acceptance criteria

- [x] Catalog refresh stores previous valid version.
- [x] Rollback restores previous valid catalog.
- [x] Corrupt model artifacts are marked corrupt and reinstalled at same version.
- [x] Model rollback is deferred pending storage policy.

## Evidence required

- [x] Catalog rollback tests.
- [x] Corrupt artifact reinstall tests.
- [x] State transition evidence.

## Blocked by

- 01

## Evidence

- `src/mery_tts/schemas/v1.py`, catalog refresh/install/verifier modules, storage identity code, and API routes implement layered versioning, catalog rollback, explicit confirmation, storage measurement, and safe cleanup.
- Console assets expose confirmation, storage advisory, and safe cleanup actions while refusing model cleanup.
- `tests/unit/test_catalog_refresh_install.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, `tests/unit/test_storage_identity.py`, and `tests/contract/test_api_core.py` cover release/update/storage lifecycle behavior.
- Verification: ADR-0044 focused verification previously recorded: release/update/storage lifecycle gate passed; current API/core verification remains green.
