# Add OpenAI-compatible speech route to the v1 REST contract

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0005 amendment — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Update the versioned REST contract so `POST /v1/audio/speech` is part of the `/v1` surface while preserving native Mery route semantics everywhere else. This issue should prepare schemas and route registration for ADR-0014 implementation.

## Acceptance criteria

- [ ] `/v1` route documentation/OpenAPI includes `POST /v1/audio/speech` as an authenticated REST endpoint.
- [ ] The speech route is clearly marked as OpenAI-compatible edge semantics, not native Mery semantics.
- [ ] Native REST and WebSocket routes remain unchanged and continue using native error shapes.
- [x] Contract tests verify route presence, auth requirement, and unsupported-method/unknown-route behavior. `tests/contract/test_openai_speech.py` covers successful `POST /v1/audio/speech`, auth-required native taxonomy envelope, unsupported `GET /v1/audio/speech`, unknown `/v1/audio/unknown`, and OpenAI-vs-native error shape separation.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Document `/v1/audio/speech` in generated OpenAPI with auth, request limits, supported formats, and OpenAI-shaped errors.
- [x] Add route-level tests for unsupported methods, unknown routes, auth failures, and native-route error shape separation. `tests/contract/test_openai_speech.py::test_openai_speech_requires_authentication`, `test_openai_speech_rejects_unsupported_method_and_unknown_route`, and `test_openai_errors_remain_separate_from_native_error_shape` pin these route-level contracts.

## Comments
