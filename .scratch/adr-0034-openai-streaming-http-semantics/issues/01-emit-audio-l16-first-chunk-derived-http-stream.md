# Emit audio/L16 first-chunk-derived HTTP stream

Status: pending

## Parent

ADR-0034 — `docs/adr/ADR-0034-openai-streaming-http-semantics.md`

## What to build

Harden `/v1/audio/speech` streaming so `stream=true + response_format=pcm` emits raw PCM with `audio/L16` response semantics, first-chunk-derived headers, and strict first-byte error behavior.

## Acceptance criteria

- [ ] Streaming response uses `audio/L16;rate=<sample_rate_hz>;channels=<channels>` derived from the first chunk.
- [ ] Response includes Mery request/audio headers for request ID, encoding, sample rate, channels, sample width, stream format, buffering, and cache policy, including `X-Accel-Buffering: no` as proxy-safe/no-op-local behavior.
- [ ] Failures before the first chunk return OpenAI-shaped JSON errors.
- [ ] Failures after the first byte terminate, cancel, and structured-log without JSON wrappers, SSE, NDJSON, trailers, or silence padding.

## Production-ready criteria

- [ ] Contract tests assert request validation and pre-first-byte error mapping.
- [ ] Real uvicorn integration tests assert headers, media type, raw bytes, ordered chunk delivery, and disconnect cleanup.
- [ ] Error tests cover first-chunk failure and post-start metadata/adapter failure.
- [ ] Tests use the real uvicorn path for true HTTP streaming behavior, not a buffered-only in-process client.

## Blocked by

- ADR-0031 issue `02-split-openai-stream-route-onto-streaming-subsystem.md`
- ADR-0032 issue `02-add-metadata-and-sequence-validation-tests.md`
- ADR-0033 issue `01-implement-pipeline-owned-cancellation.md`
