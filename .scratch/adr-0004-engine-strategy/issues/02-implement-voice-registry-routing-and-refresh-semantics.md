# Implement VoiceRegistry routing and refresh semantics

Status: ready-for-agent

## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Implement `VoiceRegistry` as the voice-to-engine routing index with copy-on-write refresh semantics, keeping WebSocket sessions decoupled from `EngineRegistry` internals.

## Acceptance criteria

- [ ] `VoiceRegistry` resolves a `voiceId` to an adapter and descriptor through a routing map.
- [ ] `refresh()` builds a new routing map and atomically swaps it without tracking active sessions.
- [ ] WebSocket-facing code can depend on `VoiceRegistry` without importing `EngineRegistry` directly.
- [ ] Tests prove active adapter references remain valid across refresh.

## Blocked by

- 01-define-engine-adapter-and-engine-registry-discovery

## Comments
