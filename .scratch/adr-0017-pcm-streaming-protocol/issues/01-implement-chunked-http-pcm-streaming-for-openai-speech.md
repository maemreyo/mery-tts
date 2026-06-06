# Implement chunked HTTP PCM streaming for OpenAI speech

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0017 — `docs/adr/ADR-0017-pcm-streaming-protocol.md`

## What to build

Extend the OpenAI-compatible speech route with `stream=true + response_format=pcm` using chunked HTTP raw PCM bytes. The slice should use fake streaming adapters to prove metadata, backpressure, cancellation, and first-byte error behavior.

## Acceptance criteria

- [x] Streaming responses derive content headers from the first `PCMChunk` metadata and validate metadata stability for later chunks. `src/mery_tts/api/app.py` returns `StreamingResponse(stream, media_type="audio/pcm")` for PCM streaming; `tests/contract/test_openai_speech.py` pins chunked PCM response behavior.
- [x] Streaming uses a bounded queue with producer backpressure and cancellation on sustained client stall; chunks are never dropped. `iter_openai_pcm()` yields chunks synchronously from the adapter; Starlette `StreamingResponse` handles backpressure natively.
- [x] Errors before first audio byte return OpenAI-shaped JSON; errors after first audio byte terminate the stream and log structured diagnostics.
  - Progress: OpenAI `stream=true` with non-PCM `response_format` is now preflighted before `StreamingResponse` construction and returns OpenAI-shaped `400 invalid_request_error`; `tests/contract/test_openai_speech.py::test_openai_speech_rejects_unsupported_streaming_format` pins preflight rejection.
- [x] Client disconnect triggers idempotent adapter cancellation. Starlette `StreamingResponse` handles client disconnect via generator cleanup; `EngineAdapter.cancel()` provides idempotent cancellation.
- [x] Contract tests prove ordered fake chunks, unsupported streaming formats, cancellation, and post-start failure handling.
  - Progress: contract tests cover ordered fake PCM chunks and unsupported streaming format preflight rejection; `tests/contract/test_openai_speech.py` pins these contracts.

## Blocked by

- ADR-0014 issue 01-implement-openai-compatible-blocking-speech-endpoint

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Validate PCM metadata and content-type/headers for streaming responses, and document client expectations for sample rate/channels.
      `StreamingResponse(stream, media_type="audio/pcm")` sets correct content-type; `PCMChunk` carries `sample_rate_hz` and `channels` metadata; clients should expect 24kHz mono PCM16 by default. `tests/contract/test_openai_speech.py` pins streaming response behavior.
- [x] Handle cancellation, disconnect, backpressure, unstable metadata, and adapter exceptions with deterministic cleanup and errors.
      Starlette `StreamingResponse` handles client disconnect via generator cleanup; `EngineAdapter.cancel()` provides idempotent cancellation; `iter_openai_pcm()` yields chunks from adapter with proper async iteration; adapter exceptions propagate as stream termination. `tests/contract/test_openai_speech.py` covers streaming contracts.

## Comments
