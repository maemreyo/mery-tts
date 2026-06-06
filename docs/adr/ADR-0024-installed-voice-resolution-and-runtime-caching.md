# ADR-0024 — Installed voice resolution and runtime caching

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Grill local-usable, Q15–Q18, Q25–Q29

## Context

Installed voices are persisted as manifests and routed through `VoiceRegistry`. Real Piper and Kokoro inference need concrete model/config paths and potentially expensive runtime objects. Coupling engine adapters directly to `RuntimePaths` or storage layout would break modularity and make tests brittle.

The first local-usable milestone also needs smoke testing and readiness tracking without loading every model at install time or on app startup.

## Decision

Keep `VoiceRegistry` lightweight. It stores manifest-level `VoiceDescriptor` routing only:

```text
voice_id → VoiceDescriptor
voice_id → engine_id/adapter route
```

It does not store absolute paths or loaded runtime objects.

Introduce an `InstalledVoiceResolver` that turns manifest descriptors into immutable resolved voices:

```python
@dataclass(frozen=True)
class ResolvedVoice:
    voice_id: str
    engine_id: str
    payload: ResolvedVoicePayload
```

For model-file providers, the resolver returns validated absolute paths:

```python
@dataclass(frozen=True)
class ResolvedModelFilePayload:
    artifact_id: str
    model_path: Path
    config_path: Path | None
```

Safety rules:

- manifests store only safe relative paths;
- resolver joins paths under the known artifact root;
- resolver calls `.resolve()` and verifies each path remains under the artifact root;
- resolver verifies required files exist and match expected roles;
- adapters receive paths read-only and never write.

Piper and Kokoro adapters lazy-load runtimes on first synthesis and cache per resolved voice/artifact. They do not load at install time and do not reload per request. Cache eviction can be bounded later; the first milestone may use a small fixed cache.

Smoke status is stored per installed voice. Engine/helper readiness is derived from per-voice readiness. Smoke uses the same synthesis path and runtime cache as real requests, with bounded side effects: smoke metadata and cache warming only, no user preference mutation.

## Rationale

- Lightweight registry refresh is cheap and safe after install/delete.
- Resolver-owned path validation keeps storage security outside engine adapters while giving adapters the file paths required by third-party libraries.
- Lazy runtime cache keeps install fast and avoids loading unused voices.
- Per-voice smoke reflects what users actually select; engine-level health alone can hide broken voice configs.
- Sharing the synthesis path for smoke prevents false confidence from a separate smoke-only implementation.

## Production-ready criteria

This ADR is production-ready only when:

- `VoiceRegistry` contains no absolute paths and no loaded runtime objects.
- `InstalledVoiceResolver` validates safe relative manifest paths and returns resolved absolute paths under artifact roots.
- Resolver tests cover traversal attempts, missing artifacts, missing config/model files, ambiguous artifacts, and valid Piper/Kokoro payloads.
- Piper/Kokoro adapters lazy-load and cache runtime objects keyed by resolved voice/artifact identity.
- Adapter tests verify runtime reuse, dependency-missing errors, model-invalid errors, and cache invalidation behavior on delete or resolver miss.
- Per-voice smoke records include status, checked timestamp, sample rate, channels, duration, and sanitized failure details.
- `mery doctor --deep` or `mery smoke` records smoke status without mutating default voice/fallback preferences.
- Health derives engine/helper summaries from voice-level resolver and smoke status.

## Consequences

**Enables:** clean storage/adapter separation, safe path handling, fast repeated synthesis, per-voice readiness, and robust tests with temp directories and fake runtimes.

**Constrains:** adapters cannot call `RuntimePaths.from_environment()` or inspect model directories directly.

## Related

- ADR-0004 — Dual-engine from day one
- ADR-0011 — Server-owned storage with platformdirs and user override
- ADR-0013 — VoiceDescriptor discriminated union
- ADR-0018 — Provider rollout strategy
- ADR-0022 — Provider fallback and synthesis orchestration
- ADR-0023 — Model install and artifact source architecture
