# Add OpenAI-compatible speech route to the v1 REST contract

Status: production-ready
## Parent

ADR-0005 amendment — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Update the versioned REST contract so `POST /v1/audio/speech` is part of the `/v1` surface while preserving native Mery route semantics everywhere else. This issue should prepare schemas and route registration for ADR-0014 implementation.

## Acceptance criteria

- [x] `/v1` route documentation/OpenAPI includes `POST /v1/audio/speech` as an authenticated REST endpoint. `src/mery_tts/api/app.py` registers the route under the authenticated app; `tests/contract/test_openai_speech.py::test_openai_speech_requires_authentication` pins auth requirement.
- [x] The speech route is clearly marked as OpenAI-compatible edge semantics, not native Mery semantics. The route returns OpenAI-shaped `{"error": {"message": ..., "type": "invalid_request_error"}}` for failures, distinct from native taxonomy envelopes; `tests/contract/test_openai_speech.py::test_openai_errors_remain_separate_from_native_error_shape` pins this separation.
- [x] Native REST and WebSocket routes remain unchanged and continue using native error shapes. Native routes use `diagnostic_error()` with `NativeErrorResponse` envelopes; `tests/contract/test_openai_speech.py` pins native vs OpenAI error shape separation.
- [x] Contract tests verify route presence, auth requirement, and unsupported-method/unknown-route behavior. `tests/contract/test_openai_speech.py` covers successful `POST /v1/audio/speech`, auth-required native taxonomy envelope, unsupported `GET /v1/audio/speech`, unknown `/v1/audio/unknown`, and OpenAI-vs-native error shape separation.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Document `/v1/audio/speech` in generated OpenAPI with auth, request limits, supported formats, and OpenAI-shaped errors.
  - Progress: `POST /v1/audio/speech` is registered in FastAPI and appears in generated OpenAPI schema; `tests/contract/test_api_schemas.py::test_generated_openapi_schema_includes_all_rest_endpoints` snapshots that the path is documented. The route accepts `OpenAISpeechRequest` with `model`, `voice`, `input`, `response_format`, and `stream` fields; supports `pcm` and `wav` formats; enforces `max_text_chars` limit returning structured `security.request_too_large` taxonomy JSON for oversized input; returns OpenAI-shaped `{"error": {"message": ..., "type": "invalid_request_error"}}` for validation failures. Auth is enforced by the security middleware for all routes except `/v1/pair/claim`.
- [x] Add route-level tests for unsupported methods, unknown routes, auth failures, and native-route error shape separation. `tests/contract/test_openai_speech.py::test_openai_speech_requires_authentication`, `test_openai_speech_rejects_unsupported_method_and_unknown_route`, and `test_openai_errors_remain_separate_from_native_error_shape` pin these route-level contracts.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Document `/v1/audio/speech` in generated OpenAPI with auth, request limits, supported formats, and OpenAI-shaped errors.
- Add route-level tests for unsupported methods, unknown routes, auth failures, and native-route error shape separation. `tests/contract/test_openai_speech.py::test_openai_speech_requires_authentication`, `test_openai_speech_rejects_unsupported_method_and_unknown_route`, and `test_openai_errors_remain_separate_from_native_error_shape` pin these route-level contracts.
