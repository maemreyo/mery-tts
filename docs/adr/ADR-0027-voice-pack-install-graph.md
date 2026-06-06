# ADR-0027 — VoicePack install graph

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Setup/install grill, RCM architecture review

## Context

Current install flows use model/catalog IDs directly. That is sufficient for early fixtures, but it does not match user intent or future provider complexity. Users want voice experiences such as "English reading" or "Vietnamese offline voice", not raw Python packages, model URLs, artifact filenames, or provider-specific IDs.

Technically, a usable voice may depend on a provider runtime, one or more artifacts, config files, smoke status, locale metadata, and synthesis defaults. A future pack may include multiple voices or shared artifacts. Flattening this into `model_id` makes install planning brittle and pushes provider knowledge into clients.

## Decision

Introduce an explicit runtime install graph:

```text
VoicePack → Voice → Artifact → ProviderRuntime
```

Definitions:

```text
ProviderRuntime
  provider dependency and execution capability, e.g. piper-plus or kokoro

Artifact
  verified local file set from bundled, HTTP, local, or future signed source

Voice
  synthesis identity exposed to clients and routed through provider adapters

VoicePack
  user-facing install unit that groups voices, artifacts, runtime requirements,
  recommendation metadata, and setup intent suitability
```

Voice Packs are the primary user-facing install object. Voices remain the synthesis-time selectable identity. Artifacts and provider runtimes remain internal install/readiness dependencies.

Existing `model_id` and `/v1/models/*` terminology may remain as backwards-compatible aliases during migration, but new setup APIs and UI should prefer `voicePackId`, `voiceId`, `artifactId`, and `providerRuntimeId`.

## Rationale

- Voice Packs match user intent better than raw models or providers.
- Explicit graph supports shared artifacts, multiple voices per pack, provider reuse, and future providers.
- Separating Voice from Artifact prevents clients from sending filesystem paths or model URLs.
- Install planning becomes deterministic and testable.
- Zam Reader can request "English reading" without knowing Kokoro/Piper internals.

## Production-ready criteria

This ADR is production-ready only when:

- Catalog data can express ProviderRuntime, Artifact, Voice, and VoicePack nodes and their relationships.
- `/v1/voice-packs` exposes user-safe pack metadata without leaking raw filesystem paths.
- Install planning resolves pack requirements into provider runtime checks and artifact/voice install steps.
- Existing `/v1/models/install` remains compatible or has a documented migration path.
- Tests cover single-voice packs, multi-voice packs, shared artifacts, missing provider runtime, missing artifact, and invalid graph relationships.

## Consequences

**Enables:** user-centric setup, scalable provider/model support, and clean install planning.

**Constrains:** implementation must stop inferring provider/voice/artifact identity from string naming conventions as the primary model.

## Related

- ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity
- ADR-0016 — Install job lifecycle
- ADR-0023 — Model install and artifact source architecture
- ADR-0024 — Installed voice resolution and runtime caching
- ADR-0026 — Standalone setup boundary and client responsibilities
