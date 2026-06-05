# Add OpenAI-compatible chunked HTTP audio sink

Status: completed

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

## Comments
