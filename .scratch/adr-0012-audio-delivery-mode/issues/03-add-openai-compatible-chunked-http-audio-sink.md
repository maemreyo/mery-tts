# Add OpenAI-compatible chunked HTTP audio sink

Status: production-ready
## Parent

ADR-0012 amendment — `docs/adr/ADR-0012-audio-delivery-mode.md`

## What to build

Add the OpenAI-compatible chunked HTTP audio sink as a separate delivery path from native WebSocket audio events. Both paths should consume the same `AsyncIterator[PCMChunk]` engine contract while keeping client populations and transport semantics distinct.

## Acceptance criteria

- [x] `stream=true + response_format=pcm` on `/v1/audio/speech` uses chunked HTTP rather than WebSocket or SSE. `src/mery_tts/api/app.py` returns `StreamingResponse(stream, media_type="audio/pcm")` for PCM streaming; `tests/contract/test_openai_speech.py` pins chunked PCM response behavior.
- [x] Native `WS /v1/events` audio delivery remains unchanged and continues emitting native event envelopes. `WS /v1/events` emits `synthesize.started`, `audio.chunk`, `audio.completed` events; `tests/unit/test_ws_and_orchestration.py` pins native event delivery.
- [x] Both delivery paths consume adapter `PCMChunk` streams without route-specific adapter changes. Both `StreamingResponse` and `synthesize_events()` consume `AsyncIterator[PCMChunk]` from engine adapters.
- [x] Tests prove WebSocket event delivery and OpenAI chunked HTTP delivery are independent and do not import each other's transport implementation. `tests/contract/test_openai_speech.py` tests HTTP chunked delivery; `tests/unit/test_ws_and_orchestration.py` tests WS event delivery; neither imports the other's transport.

## Blocked by

- ADR-0017 issue 01-implement-chunked-http-pcm-streaming-for-openai-speech

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Ensure chunked HTTP streaming propagates mid-stream adapter errors as documented and cleans up/cancels generator work on client disconnect.
  - Evidence: `src/mery_tts/api/openai/speech.py::iter_openai_pcm()` consumes adapter `AsyncIterator[PCMChunk]` directly and raises on unstable PCM metadata during iteration; `tests/contract/test_openai_speech.py::test_openai_streaming_speech_propagates_mid_stream_adapter_errors` proves mid-stream adapter failure propagates through the chunked HTTP response iterator.
- [x] Prove HTTP chunking and WebSocket audio events are independent real transports using client-level tests.
  - Evidence: `tests/contract/test_openai_speech.py::test_openai_streaming_speech_returns_ordered_pcm_chunks` and `test_openai_streaming_speech_uses_http_transport_without_ws_events` pin `audio/pcm` chunked HTTP bytes with no native event envelope; `tests/unit/test_ws_and_orchestration.py::test_ws_synthesis_events_are_ordered` separately pins native `synthesize.started`/`audio.chunk`/`audio.completed` WebSocket event semantics.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Ensure chunked HTTP streaming propagates mid-stream adapter errors as documented and cleans up/cancels generator work on client disconnect.
- Prove HTTP chunking and WebSocket audio events are independent real transports using client-level tests.
