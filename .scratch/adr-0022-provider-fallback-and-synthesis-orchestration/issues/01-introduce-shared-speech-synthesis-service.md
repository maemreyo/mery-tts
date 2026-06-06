# Introduce shared SpeechSynthesisService

Status: planned

## Parent

ADR-0022 — `docs/adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`

## What to build

Introduce a shared synthesis orchestration service used by REST, CLI, smoke, `/console`, and future WebSocket transports. Transports should adapt inputs and outputs; the service owns voice plan resolution, adapter calls, fallback, and synthesis diagnostics.

## Acceptance criteria

- [ ] REST `/v1/audio/speech` calls `SpeechSynthesisService` instead of directly resolving `VoiceRegistry` and adapters.
- [ ] CLI speech can call the same service for output/playback paths.
- [ ] Service returns a transport-neutral `SynthesisResult` with PCM chunks or bytes, selected voice, audio metadata, and diagnostics.
- [ ] Existing fake-adapter tests can exercise the service without real Piper/Kokoro dependencies.

## Production-ready criteria

- [ ] Unit tests cover successful synthesis, unsupported model/format, unknown voice, and adapter failure.
- [ ] API routes remain thin and do not contain provider/fallback policy.
- [ ] CLI and REST behavior share one service-level test fixture.

## Blocked by

- None - can start immediately
