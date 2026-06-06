# Split CLI playback and streaming audio sinks

Status: production-ready
## Parent

ADR-0012 — `docs/adr/ADR-0012-audio-delivery-mode.md`

## What to build

Implement the two audio infrastructure sinks that sit below the engine layer.
Both consume `AsyncIterator[PCMChunk]` and must never be imported from the
same module — `player.py` is CLI-only, `encoder.py` is API-only.

**`audio/player.py` — direct system audio playback**

Implement `AudioPlayer` with an async `play(stream: AsyncIterator[PCMChunk])`
method that:
1. Opens a `sounddevice.OutputStream` at the sample rate declared in the
   first `PCMChunk.sample_rate`.
2. Drains the async iterator, writing each chunk to the stream in a thread
   executor (sounddevice is blocking).
3. Closes the stream cleanly on completion or on `CancelledError`.
4. Exposes a `stop()` method that signals the drain loop to exit early and
   closes the stream immediately.

**`audio/encoder.py` — PCM16 → base64 WebSocket chunk encoder**

Implement `AudioEncoder` with a single pure function
`encode_chunk(chunk: PCMChunk) -> str` that base64-encodes the raw bytes
from a `PCMChunk` and returns the encoded string for inclusion in
`audio.chunk` WS event payloads.

**Import graph rule (enforced by depcruise):**
- `audio/player.py` may only be imported from `cli/`
- `audio/encoder.py` may only be imported from `api/ws/`
- Neither file may import the other

## Acceptance criteria

- [x] `AudioPlayer.play()` drains a `PCMChunk` async iterator to system audio
      without blocking the event loop. `tests/unit/test_audio_sinks.py::test_audio_player_drains_stream_and_stops` verifies the async iterator is drained in chunk order through the injectable write sink.
- [x] `AudioPlayer.stop()` cancels an in-progress stream without raising an
      unhandled exception. `tests/unit/test_audio_sinks.py::test_audio_player_stop_prevents_later_chunks_from_writing` verifies `stop()` prevents later chunks from being written without raising.
- [x] `AudioEncoder.encode_chunk()` produces a base64 string that, when decoded,
      exactly equals the input `PCMChunk` raw bytes. `tests/unit/test_audio_sinks.py::test_audio_encoder_round_trips_pcm_bytes` pins byte-for-byte round-trip behavior.
- [x] `audio/player.py` is not importable from `api/ws/events.py` (depcruise rule). Package-boundary tests scan API WebSocket modules and fail if they import `mery_tts.audio.player`.
- [x] `audio/encoder.py` is not importable from `cli/` (depcruise rule). Package-boundary tests scan CLI modules and fail if they import `mery_tts.audio.encoder`.
- [x] Unit tests cover: player drains full stream, player stops mid-stream,
      encoder round-trips with known fixture bytes. `tests/unit/test_audio_sinks.py` covers full player drain, stop-before-later-chunks behavior, and base64 encoder round-trip against deterministic fake sine PCM bytes.
- [x] Tests use a `FakeEngineAdapter` PCM sine wave — no real model download. `tests/unit/test_audio_sinks.py` defines a named `FakeEngineAdapter` with a preset `VoiceDescriptor` and deterministic sine-wave PCM chunks for player, encoder, and WAV exporter coverage without real engine/model downloads.

## Blocked by

- ADR-0004 issue 01 (EngineAdapter ABC + PCMChunk schema)
- ADR-0002 issue 03 (CLI playback and daemon split confirmed)

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Implement actual device playback draining PCM with sample-rate/channel handling, cancellation, and no API import dependency on speaker libraries.
  - Evidence: `src/mery_tts/audio/player.py::AudioPlayer` opens an injectable playback stream from the first `PCMChunk` sample rate/channels, writes PCM bytes through `asyncio.to_thread()`, closes on completion/stop/cancellation, and maps device failures to structured `playback.device_unavailable` errors. `SoundDeviceStream` is CLI playback-only and uses `sounddevice.OutputStream`; API/WebSocket code continues to use `AudioEncoder` and does not import `audio.player`.
- [x] Add manual/marked audio-device smoke plus fake PCM unit tests for stop/drain/error paths.
  - Evidence: `tests/unit/test_audio_sinks.py::test_audio_player_drains_stream_and_stops`, `test_audio_player_stop_prevents_later_chunks_from_writing`, `test_audio_player_closes_stream_on_cancellation`, and `test_audio_player_maps_device_failure_to_structured_error` cover fake PCM drain/stop/cancel/error paths without hardware. `test_audio_player_real_device_smoke_is_marked_and_skipped_by_default` is marked `engine` and skips cleanly unless manually enabled with local audio hardware.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Implement actual device playback draining PCM with sample-rate/channel handling, cancellation, and no API import dependency on speaker libraries.
- Add manual/marked audio-device smoke plus fake PCM unit tests for stop/drain/error paths.
