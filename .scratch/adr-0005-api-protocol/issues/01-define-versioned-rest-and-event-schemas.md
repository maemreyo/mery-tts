# Define versioned REST and event schemas

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Define versioned Pydantic schemas for `/v1` REST responses, requests, WebSocket envelopes, install events, synthesis events, PCM chunks, and common correlation fields.

## Acceptance criteria

- [x] REST schemas cover health, engines, installed voices, catalog voices, model install/status/delete, storage, diagnostics, and pairing. `tests/contract/test_api_schemas.py::test_rest_schema_contracts_include_version_and_correlation_fields` instantiates the current REST request/response schema set and asserts version/correlation fields.
- [x] WebSocket schemas cover `install.*`, `synthesize.*`, `audio.*`, and `helper.statusChanged` event types. `tests/contract/test_api_schemas.py::test_event_schema_contracts_cover_install_synthesis_audio_and_helper_status` covers install, synthesis, audio, and helper status event envelopes.
- [x] Every public response/event includes schema version and correlation metadata such as request, job, or session identifiers. Schema contract tests assert `schema_version == "v1"`, `request_id`, and event-specific `job_id`/`session_id`/chunk metadata for current schemas.
- [x] Schema tests or snapshots prove the contract is stable and OpenAPI-compatible where applicable. `tests/contract/test_api_schemas.py::test_generated_openapi_schema_exposes_version_and_correlation_fields` snapshots generated `create_app().openapi()` component refs for current `/v1` REST schemas and asserts `schema_version`/`request_id` contract fields.

## Blocked by

- ADR-0010 issue 01-define-structured-error-taxonomy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Generate or snapshot the OpenAPI schema and native WebSocket event schemas from the actual app, including error envelopes and correlation IDs.
  - Progress: `tests/contract/test_api_schemas.py` now snapshots the current Pydantic REST and native event schema objects for stable version/correlation fields; `test_generated_openapi_schema_exposes_version_and_correlation_fields` snapshots generated `create_app().openapi()` component refs for `/v1` REST success schemas; `test_generated_openapi_schema_documents_native_error_envelope` snapshots generated 401/403/413 native taxonomy error-envelope refs for authenticated `/v1` REST routes (`/v1/health` and `/v1/models/install`) and confirms 400 is not documented as a native error envelope; `test_generated_openapi_schema_includes_all_rest_endpoints` snapshots that OpenAPI documents all `/v1` REST endpoints including `/v1/audio/speech`, `/v1/pair/claim`, `/v1/diagnostics`, `/v1/storage`, `/v1/catalog/voices`, `/v1/voices/installed`, `/v1/engines`, `/v1/health`, and `/v1/models/{model_id}`. Generated native WebSocket event schema coverage remains as a future enhancement since FastAPI WebSocket routes are not included in OpenAPI by default.
- [x] Ensure every route/event returns stable `schema_version` plus request/job/session identifiers under success and failure conditions.
  - Progress: schema objects now require `schema_version` and `request_id`, and event schema tests cover `job_id`, `session_id`, and audio chunk correlation metadata. `tests/contract/test_api_core.py::test_unknown_origin_and_oversized_request_are_rejected` now pins 403 origin rejection, malformed `Content-Length` 400 failures, and 413 request-size failures to native taxonomy envelopes with `request_id="local"`. `tests/unit/test_ws_and_orchestration.py::test_ws_synthesis_events_are_ordered` now pins generated synthesis/audio events to `schema_version="v1"`, explicit `request_id`, stable `session_id`, and schema-aligned `audio.completed`. All REST routes return versioned responses with `request_id="local"`; all WebSocket events include `schema_version`, `request_id`, and `session_id`.

## Comments
