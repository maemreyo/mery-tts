# Split CLI playback and streaming audio sinks

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Define the shared PCM data contract and separate output adapters for CLI direct playback and WebSocket PCM16 chunk encoding.

## Acceptance criteria

- [ ] Shared PCM data structures are reusable by both CLI playback and WebSocket streaming.
- [ ] CLI playback code is isolated from WebSocket encoding code.
- [ ] WebSocket encoding produces PCM16/base64 chunk payloads without requiring a local speaker device.
- [ ] Tests prove both sinks consume the same synthesized PCM contract.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Wire CLI playback and WebSocket/HTTP streaming to the same real adapter `PCMChunk` source while keeping player-only dependencies out of API modules.
- [ ] Add import-boundary tests plus a fake-stream real-surface test proving playback/export/streaming consume identical PCM metadata.

## Comments
