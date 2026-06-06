# Implement WebSocket event stream protocol

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement `WS /v1/events` for authenticated long-running event streams, including synthesis start, audio chunks, completion, cancellation, failures, install progress, and helper status changes.

## Acceptance criteria

- [ ] WebSocket handshake validates the same auth token model as REST using transport-appropriate metadata.
- [ ] Synthesis requests emit ordered `synthesize.started`, one or more `audio.chunk`, and `audio.done` events.
- [ ] Cancellation emits `synthesize.cancelled` and stops further audio chunks for the session.
- [ ] WebSocket event-order tests cover success, cancellation, auth rejection, and failure mapping.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0002 issue 03-split-cli-playback-and-streaming-audio-sinks
- ADR-0004 issue 02-implement-voice-registry-routing-and-refresh-semantics
- ADR-0006 issue 02-add-auth-origin-rate-and-size-middleware

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Mount authenticated `WS /v1/events` in FastAPI with token/subprotocol validation, heartbeat/status events, and structured close/error behavior.
  - Progress: `tests/contract/test_api_core.py::test_websocket_events_accepts_valid_handshake` now pins the mounted `/v1/events` handshake to a versioned `helper.statusChanged` event with `request_id="local"` and `status="ok"`; auth/origin rejection tests cover transport close behavior. Subprotocol validation, heartbeat behavior, and structured close/error payloads remain pending.
- [ ] Add real WebSocket client tests for install, synthesize, audio chunks, cancellation, and auth failure paths.

## Comments
