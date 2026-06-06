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

- [x] Hydrate `VoiceRegistry` from installed voice manifests and bundled/remote catalog projections during startup and after install/delete commits.
  - Evidence: `src/mery_tts/api/app.py` hydrates installed voice manifests at startup and now uses `voice_registry.refresh()` after install/delete commits so stale routes are removed atomically; catalog projections remain visible through `/v1/catalog/voices` while only installed/routable descriptors enter the synthesis route map. `tests/contract/test_openai_speech.py::test_app_startup_hydrates_installed_voice_manifest_into_routing_map` pins startup route hydration and `test_delete_commit_refresh_removes_voice_route_from_registry` pins delete commit route removal; `tests/unit/test_engine_registry.py::test_voice_registry_refresh_swaps_routes_without_invalidating_old_adapter` pins atomic route swapping.
- [x] Prove refresh is atomic under active synthesis by testing old route references stay valid while new routes become visible.

## Comments
