# Explicit update confirmation and integrity policy

Status: completed

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Require explicit user/admin action for catalog refresh and model downloads with checksum/signature validation and policy checks.

## Acceptance criteria

- [x] No silent app/catalog/model auto-update occurs.
- [x] Console/CLI show source, size, license, version, and capability impact before install.
- [x] `local_only` and `air_gapped` block network updates.
- [x] Checksum/signature validation failures are structured and recoverable.

## Evidence required

- [x] CLI/Console confirmation tests.
- [x] Integrity validation tests.
- [x] Network-policy enforcement tests.

## Blocked by

- 01

## Evidence

- `src/mery_tts/schemas/v1.py`, catalog refresh/install/verifier modules, storage identity code, and API routes implement layered versioning, catalog rollback, explicit confirmation, storage measurement, and safe cleanup.
- Console assets expose confirmation, storage advisory, and safe cleanup actions while refusing model cleanup.
- `tests/unit/test_catalog_refresh_install.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, `tests/unit/test_storage_identity.py`, and `tests/contract/test_api_core.py` cover release/update/storage lifecycle behavior.
- Verification: ADR-0044 focused verification previously recorded: release/update/storage lifecycle gate passed; current API/core verification remains green.
