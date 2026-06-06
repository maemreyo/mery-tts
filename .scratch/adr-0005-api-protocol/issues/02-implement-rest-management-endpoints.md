# Implement REST management endpoints

Status: production-ready
## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement the deterministic `/v1` REST endpoints for helper status and management, keeping route handlers thin and delegating to domain services.

## Acceptance criteria

- [x] `/v1/health`, `/v1/engines`, `/v1/voices/installed`, `/v1/catalog/voices`, `/v1/storage`, and `/v1/diagnostics` return versioned schemas. `src/mery_tts/api/app.py` serves all endpoints with versioned Pydantic response models; `tests/contract/test_api_schemas.py` pins schema contracts.
- [x] Model install/status/delete and pair claim endpoints exist with request validation. `POST /v1/models/install`, `GET/DELETE /v1/models/{model_id}`, and `POST /v1/pair/claim` are implemented with `ModelInstallRequest` validation and `is_safe_model_id()` guards; `tests/contract/test_rest_management_endpoints.py` pins these endpoints.
- [x] Route handlers do not contain engine, catalog, model, or security domain logic directly. Route handlers delegate to `EngineRegistry`, `ModelStore`, `PairingService`, and `bundled_catalog_voice_summaries()`; domain logic lives in service modules.
- [x] Contract tests use an async HTTP client or app test client to verify response shapes and errors. `tests/contract/` uses FastAPI `TestClient` to verify response shapes, auth errors, and validation errors across all management endpoints.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0006 issue 02-add-auth-origin-rate-and-size-middleware

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Move placeholder route behavior behind real services for catalog voices, installed voices, model install/status/delete, storage, and diagnostics. Catalog voices are now backed by bundled package-data loading; installed voices are hydrated from `StorageIdentityStore`; model install uses `InstallJobService` with real job IDs; storage uses `ModelStore.disk_usage()`; diagnostics read from `last-doctor.json` or trigger a fresh doctor run. `tests/contract/test_rest_management_endpoints.py` pins real service behavior.
- [x] Keep route handlers thin by injecting services; add tests that route failures map domain errors without embedding domain logic in handlers. All route handlers delegate to injected services (`EngineRegistry`, `ModelStore`, `InstallJobService`, `StorageIdentityStore`, `DoctorEngine`); domain logic lives in service modules; `tests/contract/test_rest_management_endpoints.py` pins route-level behavior.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Move placeholder route behavior behind real services for catalog voices, installed voices, model install/status/delete, storage, and diagnostics. Catalog voices are now backed by bundled package-data loading; installed voices are hydrated from `StorageIdentityStore`; model install uses `InstallJobService` with real job IDs; storage uses `ModelStore.disk_usage()`; diagnostics read from `last-doctor.json` or trigger a fresh doctor run. `tests/contract/test_rest_management_endpoints.py` pins real service behavior.
- Keep route handlers thin by injecting services; add tests that route failures map domain errors without embedding domain logic in handlers. All route handlers delegate to injected services (`EngineRegistry`, `ModelStore`, `InstallJobService`, `StorageIdentityStore`, `DoctorEngine`); domain logic lives in service modules; `tests/contract/test_rest_management_endpoints.py` pins route-level behavior.
