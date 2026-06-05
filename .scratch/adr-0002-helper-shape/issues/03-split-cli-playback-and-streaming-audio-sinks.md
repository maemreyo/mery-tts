# Split CLI playback and streaming audio sinks

Status: ready-for-agent

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

## Comments
