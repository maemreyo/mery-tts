# Introduce shared SpeechSynthesisService

Status: completed

## Parent

ADR-0022 — `docs/adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`

## What to build

Introduce a shared synthesis orchestration service used by REST, CLI, smoke, `/console`, and future WebSocket transports. Transports should adapt inputs and outputs; the service owns voice plan resolution, adapter calls, fallback, and synthesis diagnostics.

## Acceptance criteria

- [x] REST `/v1/audio/speech` calls `SpeechSynthesisService` instead of directly resolving `VoiceRegistry` and adapters.
- [x] CLI speech can call the same service for output/playback paths.
- [x] Service returns a transport-neutral `SynthesisResult` with PCM chunks or bytes, selected voice, audio metadata, and diagnostics.
- [x] Existing fake-adapter tests can exercise the service without real Piper/Kokoro dependencies.

## Production-ready criteria

- [x] Unit tests cover successful synthesis, unsupported model/format, unknown voice, and adapter failure.
- [x] API routes remain thin and do not contain provider/fallback policy.
- [x] CLI and REST behavior share one service-level test fixture.

## Blocked by

- None - can start immediately
