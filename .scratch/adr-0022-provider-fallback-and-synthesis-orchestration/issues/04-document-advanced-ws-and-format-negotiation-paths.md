# Document advanced WS and format negotiation paths

Status: completed

## Parent

ADR-0022 — `docs/adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`

## What to build

Document advanced synthesis paths not required for the first HTTP usable milestone: WebSocket streaming diagnostics, strict sample-rate negotiation, future compressed formats, and bidirectional cancellation behavior.

## Acceptance criteria

- [x] Docs describe how future WebSocket transport reuses `SpeechSynthesisService` instead of duplicating orchestration.
- [x] Docs define how `audio.chunk` events carry encoding/sampleRate/channels/dataBase64 metadata.
- [x] Docs state that fallback preserves requested response format and reports actual PCM metadata.
- [x] Docs list future strict sample-rate/channel negotiation behavior and failure mode.

## Production-ready criteria

- [x] Future work is captured as explicit issues and not treated as complete by HTTP milestone tests.
- [x] ADR-0022 cross-links ADR-0017 and ADR-0021 deferral language.

## Documentation

This document captures advanced synthesis paths that are not required for the first HTTP usable milestone.

### WebSocket transport architecture

The future WebSocket transport reuses the existing `SpeechSynthesisService` rather than duplicating orchestration logic. This ensures consistent behavior between HTTP and WebSocket transports.

### Audio chunk events

When streaming via WebSocket, `audio.chunk` events include metadata for consumer processing:

- `encoding` — the audio encoding format
- `sampleRate` — samples per second
- `channels` — mono or stereo
- `dataBase64` — the audio data payload

### Format negotiation

When a fallback occurs due to provider unavailability, the system preserves the requested response format where possible. The actual PCM metadata is reported back to the client so it can adapt playback.

### Strict sample-rate negotiation (future)

Future production hardening will include strict sample-rate and channel negotiation. If the requested sample rate is not available, the request will fail rather than auto-downsampling. This gives clients precise control but requires explicit error handling.

### Related deferrals

This work relates to the WebSocket streaming deferral documented in ADR-0021. ADR-0017 provides the foundational synthesis service architecture.

## Blocked by

- None - documentation can start immediately
