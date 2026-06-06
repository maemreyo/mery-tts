# Document cache eviction and runtime resource hardening

Status: future

## Parent

ADR-0024 — `docs/adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`

## What to build

Document advanced runtime-cache hardening: bounded eviction, explicit unload, memory pressure behavior, concurrent synthesis limits, warmup strategy, and cache invalidation on artifact delete.

## Acceptance criteria

- [ ] Docs define cache keys by engine, artifact, resolved path/config identity, and runtime dependency version where needed.
- [ ] Future eviction policy covers max loaded voices and deterministic unload behavior.
- [ ] Delete/invalidation rules specify how cached runtimes become unusable after artifact removal.
- [ ] Concurrency limits and timeout behavior are listed as future production hardening.

## Production-ready criteria

- [ ] Future cache-hardening issue is actionable without changing first milestone cache interface.
- [ ] First milestone docs explicitly allow a small fixed cache while deferring advanced eviction.

## Blocked by

- None - documentation can start immediately
