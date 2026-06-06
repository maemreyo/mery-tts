# Upgrade PCMChunk with streaming metadata

Status: pending

## Parent

ADR-0032 — `docs/adr/ADR-0032-pcm-chunk-streaming-contract.md`

## What to build

Evolve the shared `PCMChunk` contract so every audio-producing path carries enough metadata for streaming headers, validation, and transport reuse while keeping existing adapter call sites stable through safe defaults.

## Acceptance criteria

- [ ] `PCMChunk` includes sample width, encoding, and sequence metadata with backward-compatible defaults.
- [ ] Encoding taxonomy supports `pcm_s16le` and `pcm_f32le` internally, while documenting `pcm_s16le` as the only P1 HTTP streaming format.
- [ ] PiperPlus, Kokoro, fake adapters, audio encoder, export, CLI playback, and WebSocket event paths accept the richer chunk shape.
- [ ] No parallel streaming-only chunk type is introduced.
- [ ] Existing blocking PCM and WAV behavior remains unchanged.

## Production-ready criteria

- [ ] Unit tests cover default metadata values, explicit metadata values, and allowed encoding values.
- [ ] Type checks pass without suppressing errors.
- [ ] Existing synthesis/export/playback tests pass with richer chunks.

## Blocked by

- None - can start immediately
