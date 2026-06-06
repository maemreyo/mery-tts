# Document advanced WS and format negotiation paths

Status: future

## Parent

ADR-0022 — `docs/adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`

## What to build

Document advanced synthesis paths not required for the first HTTP usable milestone: WebSocket streaming diagnostics, strict sample-rate negotiation, future compressed formats, and bidirectional cancellation behavior.

## Acceptance criteria

- [ ] Docs describe how future WebSocket transport reuses `SpeechSynthesisService` instead of duplicating orchestration.
- [ ] Docs define how `audio.chunk` events carry encoding/sampleRate/channels/dataBase64 metadata.
- [ ] Docs state that fallback preserves requested response format and reports actual PCM metadata.
- [ ] Docs list future strict sample-rate/channel negotiation behavior and failure mode.

## Production-ready criteria

- [ ] Future work is captured as explicit issues and not treated as complete by HTTP milestone tests.
- [ ] ADR-0022 cross-links ADR-0017 and ADR-0021 deferral language.

## Blocked by

- None - documentation can start immediately
