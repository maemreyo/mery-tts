# Implement VoiceRegistry routing and refresh semantics

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Implement `VoiceRegistry` as the voice-to-engine routing index with copy-on-write refresh semantics, keeping WebSocket sessions decoupled from `EngineRegistry` internals.

## Acceptance criteria

- [x] `VoiceRegistry` resolves a `voiceId` to an adapter and descriptor through a routing map.
- [x] `refresh()` builds a new routing map and atomically swaps it without tracking active sessions.
- [x] WebSocket-facing code can depend on `VoiceRegistry` without importing `EngineRegistry` directly.
- [x] Tests prove active adapter references remain valid across refresh.

## Blocked by

- 01-define-engine-adapter-and-engine-registry-discovery

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Hydrate `VoiceRegistry` from installed voice manifests and bundled/remote catalog projections during startup and after install/delete commits. Installed voice manifests are now hydrated for `/v1/voices/installed`; routing-map refresh from manifests and catalog projections remains for the synthesis/install lifecycle slice.
- [x] Prove refresh is atomic under active synthesis by testing old route references stay valid while new routes become visible.

## Comments
