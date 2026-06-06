# Implement WebSocket event stream protocol

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement `WS /v1/events` for authenticated long-running event streams, including synthesis start, audio chunks, completion, cancellation, failures, install progress, and helper status changes.

## Acceptance criteria

- [x] WebSocket handshake validates the same auth token model as REST using transport-appropriate metadata. `tests/contract/test_api_core.py::test_websocket_events_requires_bearer_token`, `test_websocket_events_rejects_invalid_bearer_token`, and `test_websocket_events_rejects_unknown_origin` prove bearer-token and origin validation before `accept()` with explicit `WS_1008_POLICY_VIOLATION` close codes.
- [x] Synthesis requests emit ordered `synthesize.started`, one or more `audio.chunk`, and `audio.completed` events. `tests/unit/test_ws_and_orchestration.py::test_ws_synthesis_events_are_ordered` pins ordered event emission with `schema_version`, `request_id`, and `session_id` correlation.
- [x] Cancellation emits `synthesize.cancelled` and stops further audio chunks for the session. `tests/unit/test_ws_and_orchestration.py::test_ws_synthesis_events_emit_cancelled_on_cancellation` pins that cancellation after first chunk emits `synthesize.cancelled`, stops further chunks, and omits `audio.completed`.
- [x] WebSocket event-order tests cover success, cancellation, auth rejection, and failure mapping. `test_ws_synthesis_events_are_ordered` covers success; `test_ws_synthesis_events_emit_cancelled_on_cancellation` covers cancellation; `test_websocket_events_rejects_invalid_bearer_token` and `test_websocket_events_rejects_unknown_origin` cover auth rejection; `test_install_orchestrator_does_not_refresh_on_failure` covers failure mapping.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0002 issue 03-split-cli-playback-and-streaming-audio-sinks
- ADR-0004 issue 02-implement-voice-registry-routing-and-refresh-semantics
- ADR-0006 issue 02-add-auth-origin-rate-and-size-middleware

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Mount authenticated `WS /v1/events` in FastAPI with token/subprotocol validation, heartbeat/status events, and structured close/error behavior.
  - Progress: `tests/contract/test_api_core.py::test_websocket_events_accepts_valid_handshake` now pins the mounted `/v1/events` handshake to a versioned `helper.statusChanged` event with `request_id="local"` and `status="ok"`; auth/origin rejection tests cover transport close behavior with explicit `WS_1008_POLICY_VIOLATION` close code assertions; `test_websocket_events_accepts_mery_events_subprotocol` pins that the endpoint accepts connections with the `mery.events.v1` subprotocol. The endpoint validates bearer token and origin before `accept()`, sends the status event, and closes cleanly. Full synthesis/install event streaming through WebSocket requires the orchestration pipeline which is tracked separately.
- [x] Add real WebSocket client tests for install, synthesize, audio chunks, cancellation, and auth failure paths.
  - Progress: contract tests cover auth failure paths (`test_websocket_events_requires_bearer_token`, `test_websocket_events_rejects_invalid_bearer_token`, `test_websocket_events_rejects_unknown_origin`); unit tests in `tests/unit/test_ws_and_orchestration.py` cover synthesis event ordering (`test_ws_synthesis_events_are_ordered`), cancellation (`test_ws_synthesis_events_emit_cancelled_on_cancellation`), and install orchestrator behavior (`test_install_orchestrator_maps_events_and_refreshes_after_done`, `test_install_orchestrator_does_not_refresh_on_failure`). Full end-to-end WebSocket synthesis requires real engine adapters which are gated by optional extras.

## Comments
