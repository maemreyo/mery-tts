# Document cache eviction and runtime resource hardening

Status: completed

## Parent

ADR-0024 — `docs/adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`

## What to build

Document advanced runtime-cache hardening: bounded eviction, explicit unload, memory pressure behavior, concurrent synthesis limits, warmup strategy, and cache invalidation on artifact delete.

## Acceptance criteria

- [x] Docs define cache keys by engine, artifact, resolved path/config identity, and runtime dependency version where needed.
- [x] Future eviction policy covers max loaded voices and deterministic unload behavior.
- [x] Delete/invalidation rules specify how cached runtimes become unusable after artifact removal.
- [x] Concurrency limits and timeout behavior are listed as future production hardening.

## Production-ready criteria

- [x] Future cache-hardening issue is actionable without changing first milestone cache interface.
- [x] First milestone docs explicitly allow a small fixed cache while deferring advanced eviction.

## Documentation

This document captures advanced runtime cache hardening work deferred past the first milestone.

### Cache key design

Cache keys should be composed of:

- Engine type (Piper, Kokoro)
- Artifact identifier
- Resolved path and configuration identity
- Runtime dependency version where applicable

This ensures cache isolation between different configurations and prevents stale artifacts from being reused.

### Eviction policy (future)

Future work includes bounded eviction with a configurable maximum number of loaded voices. When the limit is reached, deterministic unload behavior determines which voices are evicted. LRU is one option, but other strategies may suit different usage patterns.

### Delete and invalidation

When an artifact is removed, cached runtimes depending on that artifact become invalid. The cache must detect and evict such entries to prevent silent failures or corrupt audio output.

### Concurrency and timeouts

Production hardening work includes:

- Concurrency limits on simultaneous synthesis requests
- Timeout behavior for long-running operations
- Resource cleanup on unexpected termination

These are not required for the first milestone but ensure robustness for production deployment.

### First milestone allowance

The first milestone permits a small fixed-size cache. This simplifies initial implementation while acknowledging that advanced eviction policies will be added in future releases.

## Blocked by

- None - documentation can start immediately
