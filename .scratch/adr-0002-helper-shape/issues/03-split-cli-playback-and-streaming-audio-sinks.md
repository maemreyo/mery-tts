# Split CLI playback and streaming audio sinks

Status: production-ready
## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Define the shared PCM data contract and separate output adapters for CLI direct playback and WebSocket PCM16 chunk encoding.

## Acceptance criteria

- [x] Shared PCM data structures are reusable by both CLI playback and WebSocket streaming. `PCMChunk(pcm, sample_rate_hz, channels)` in `src/mery_tts/engines/base.py` is consumed by `AudioPlayer`, `AudioEncoder`, `AudioExporter`, and `synthesize_events()`.
- [x] CLI playback code is isolated from WebSocket encoding code. `audio/player.py` is CLI-only; `audio/encoder.py` is API-only; `tests/unit/test_package_boundary.py` pins import isolation.
- [x] WebSocket encoding produces PCM16/base64 chunk payloads without requiring a local speaker device. `AudioEncoder.encode_chunk()` produces base64-encoded PCM bytes; `tests/unit/test_audio_sinks.py::test_audio_encoder_round_trips_pcm_bytes` pins round-trip behavior.
- [x] Tests prove both sinks consume the same synthesized PCM contract. `tests/unit/test_audio_sinks.py` uses `FakeEngineAdapter` with deterministic sine-wave `PCMChunk` for player, encoder, and exporter tests.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Wire CLI playback and WebSocket/HTTP streaming to the same real adapter `PCMChunk` source while keeping player-only dependencies out of API modules.
  - Progress: `PCMChunk` from `src/mery_tts/engines/base.py` is the shared contract consumed by `AudioPlayer` (CLI-only), `AudioEncoder` (API-only), `AudioExporter` (CLI-only), and `synthesize_events()` (API). `iter_openai_pcm()` yields `chunk.pcm` bytes from adapter synthesis; `synthesize_events()` yields base64-encoded chunks via `AudioEncoder.encode_chunk()`. Player-only dependencies (`sounddevice`) are never imported from API modules.
- [x] Add import-boundary tests plus a fake-stream real-surface test proving playback/export/streaming consume identical PCM metadata.
  - Progress: `tests/unit/test_package_boundary.py` pins import isolation between CLI and API modules; `tests/unit/test_audio_sinks.py` uses `FakeEngineAdapter` with deterministic sine-wave `PCMChunk` for player drain, stop, encoder round-trip, and WAV exporter tests; `tests/unit/test_ws_and_orchestration.py::test_ws_synthesis_events_are_ordered` pins that synthesis events consume identical `PCMChunk` metadata (sample_rate_hz, channels) across the streaming pipeline.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Wire CLI playback and WebSocket/HTTP streaming to the same real adapter `PCMChunk` source while keeping player-only dependencies out of API modules.
- Add import-boundary tests plus a fake-stream real-surface test proving playback/export/streaming consume identical PCM metadata.
