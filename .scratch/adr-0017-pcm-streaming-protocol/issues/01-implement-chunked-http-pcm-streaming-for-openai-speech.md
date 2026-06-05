# Implement chunked HTTP PCM streaming for OpenAI speech

Status: ready-for-agent

## Parent

ADR-0017 — `docs/adr/ADR-0017-pcm-streaming-protocol.md`

## What to build

Extend the OpenAI-compatible speech route with `stream=true + response_format=pcm` using chunked HTTP raw PCM bytes. The slice should use fake streaming adapters to prove metadata, backpressure, cancellation, and first-byte error behavior.

## Acceptance criteria

- [ ] Streaming responses derive content headers from the first `PCMChunk` metadata and validate metadata stability for later chunks.
- [ ] Streaming uses a bounded queue with producer backpressure and cancellation on sustained client stall; chunks are never dropped.
- [ ] Errors before first audio byte return OpenAI-shaped JSON; errors after first audio byte terminate the stream and log structured diagnostics.
- [ ] Client disconnect triggers idempotent adapter cancellation.
- [ ] Contract tests prove ordered fake chunks, unsupported streaming formats, cancellation, and post-start failure handling.

## Blocked by

- ADR-0014 issue 01-implement-openai-compatible-blocking-speech-endpoint

## Comments
