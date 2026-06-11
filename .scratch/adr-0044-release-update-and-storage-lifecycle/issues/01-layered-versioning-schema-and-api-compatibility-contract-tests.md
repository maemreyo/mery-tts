# Layered versioning schema and API compatibility contract tests

Status: completed

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Define app, API, catalog, voice pack, and provider capability version layers with additive `/v1` compatibility guarantees.

## Acceptance criteria

- [x] Version layers are documented and exposed where needed.
- [x] `/v1` is additive-only for fields and preserves error envelope and binary response semantics.
- [x] Older clients ignore additive fields safely.
- [x] Compatibility tests cover representative old payloads.

## Evidence required

- [x] Version schema/docs excerpt.
- [x] API contract tests.
- [x] Old-client fixture tests.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/schemas/v1.py`, catalog refresh/install/verifier modules, storage identity code, and API routes implement layered versioning, catalog rollback, explicit confirmation, storage measurement, and safe cleanup.
- Console assets expose confirmation, storage advisory, and safe cleanup actions while refusing model cleanup.
- `tests/unit/test_catalog_refresh_install.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, `tests/unit/test_storage_identity.py`, and `tests/contract/test_api_core.py` cover release/update/storage lifecycle behavior.
- Verification: ADR-0044 focused verification previously recorded: release/update/storage lifecycle gate passed; current API/core verification remains green.
