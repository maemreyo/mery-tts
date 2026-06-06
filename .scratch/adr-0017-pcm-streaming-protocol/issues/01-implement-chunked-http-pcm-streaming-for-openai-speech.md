# Implement chunked HTTP PCM streaming for OpenAI speech

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0017 — `docs/adr/ADR-0017-pcm-streaming-protocol.md`

## What to build

Extend the OpenAI-compatible speech route with `stream=true + response_format=pcm` using chunked HTTP raw PCM bytes. The slice should use fake streaming adapters to prove metadata, backpressure, cancellation, and first-byte error behavior.

## Acceptance criteria

- [ ] Streaming responses derive content headers from the first `PCMChunk` metadata and validate metadata stability for later chunks.
- [ ] Streaming uses a bounded queue with producer backpressure and cancellation on sustained client stall; chunks are never dropped.
- [ ] Errors before first audio byte return OpenAI-shaped JSON; errors after first audio byte terminate the stream and log structured diagnostics.
  - Progress: OpenAI `stream=true` with non-PCM `response_format` is now preflighted before `StreamingResponse` construction and returns OpenAI-shaped `400 invalid_request_error`; post-start adapter errors remain pending.
- [ ] Client disconnect triggers idempotent adapter cancellation.
- [ ] Contract tests prove ordered fake chunks, unsupported streaming formats, cancellation, and post-start failure handling.
  - Progress: contract tests cover ordered fake PCM chunks and unsupported streaming format preflight rejection; cancellation and post-start failure handling remain pending.

## Blocked by

- ADR-0014 issue 01-implement-openai-compatible-blocking-speech-endpoint

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Validate PCM metadata and content-type/headers for streaming responses, and document client expectations for sample rate/channels.
- [ ] Handle cancellation, disconnect, backpressure, unstable metadata, and adapter exceptions with deterministic cleanup and errors.

## Comments
