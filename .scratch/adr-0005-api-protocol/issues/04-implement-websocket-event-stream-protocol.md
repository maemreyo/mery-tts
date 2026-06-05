# Implement WebSocket event stream protocol

Status: completed

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

## Comments
