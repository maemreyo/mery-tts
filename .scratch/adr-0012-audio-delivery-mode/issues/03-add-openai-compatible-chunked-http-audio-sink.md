# Add OpenAI-compatible chunked HTTP audio sink

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0012 amendment — `docs/adr/ADR-0012-audio-delivery-mode.md`

## What to build

Add the OpenAI-compatible chunked HTTP audio sink as a separate delivery path from native WebSocket audio events. Both paths should consume the same `AsyncIterator[PCMChunk]` engine contract while keeping client populations and transport semantics distinct.

## Acceptance criteria

- [ ] `stream=true + response_format=pcm` on `/v1/audio/speech` uses chunked HTTP rather than WebSocket or SSE.
- [ ] Native `WS /v1/events` audio delivery remains unchanged and continues emitting native event envelopes.
- [ ] Both delivery paths consume adapter `PCMChunk` streams without route-specific adapter changes.
- [ ] Tests prove WebSocket event delivery and OpenAI chunked HTTP delivery are independent and do not import each other's transport implementation.

## Blocked by

- ADR-0017 issue 01-implement-chunked-http-pcm-streaming-for-openai-speech

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Ensure chunked HTTP streaming propagates mid-stream adapter errors as documented and cleans up/cancels generator work on client disconnect.
  - Progress: unsupported non-PCM streaming requests are now rejected before chunked HTTP response construction with OpenAI-shaped `400 invalid_request_error`; mid-stream adapter error propagation and disconnect cleanup remain pending.
- [ ] Prove HTTP chunking and WebSocket audio events are independent real transports using client-level tests.
  - Progress: client-level OpenAI streaming tests cover chunked HTTP PCM responses and preflight streaming-format rejection while `/v1/events` handshake tests remain separate; fuller transport-independence coverage remains pending.

## Comments
