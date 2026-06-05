# Split CLI playback and streaming audio sinks

Status: completed

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

- [ ] `AudioPlayer.play()` drains a `PCMChunk` async iterator to system audio
      without blocking the event loop.
- [ ] `AudioPlayer.stop()` cancels an in-progress stream without raising an
      unhandled exception.
- [ ] `AudioEncoder.encode_chunk()` produces a base64 string that, when decoded,
      exactly equals the input `PCMChunk` raw bytes.
- [ ] `audio/player.py` is not importable from `api/ws/events.py` (depcruise rule).
- [ ] `audio/encoder.py` is not importable from `cli/` (depcruise rule).
- [ ] Unit tests cover: player drains full stream, player stops mid-stream,
      encoder round-trips with known fixture bytes.
- [ ] Tests use a `FakeEngineAdapter` PCM sine wave — no real model download.

## Blocked by

- ADR-0004 issue 01 (EngineAdapter ABC + PCMChunk schema)
- ADR-0002 issue 03 (CLI playback and daemon split confirmed)

## Comments
