# ADR-0019 — Provider adapter taxonomy

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 06

## Context

The roadmap includes many provider candidates. Per-provider routes, install logic, registry logic, or web-console behavior would make the platform unmaintainable. Providers need to plug into a small set of adapter families with clear base/provider boundaries.

## Decision

Every provider must fit this lifecycle before it is platform-integrated:

```text
CatalogVoice entry
-> artifact refs
-> installed voice manifest
-> VoiceRegistry hydration
-> VoiceDescriptor
-> EngineAdapter.synthesize()
```

Use six adapter families:

```text
preset/shared-artifact
model-file
embedding / voice-conversion
reference / zero-shot cloning
designed / prompt-driven
dialogue / multi-speaker
```

The base platform owns routes, registry, catalog repository, install job service, artifact store, voice store, garbage collection, OpenAI error mapping, and web-console API consumption. Provider-specific code owns adapter implementation, model runner, optional dependency handling, payload interpretation, catalog entries, marked tests, and provider docs.

Provider-specific logic must not leak into API routes, `InstallJobService` state machine, core storage layout, `VoiceStore` manifest format, OpenAI alias resolver logic beyond data config, or web-console feature logic.

Reference/zero-shot voices require a governance and consent design before user-created reference voices become first-class. Dialogue engines must not be forced into `/v1/audio/speech` unless a clean single-speaker mode exists.

## Rationale

- Adapter families prevent provider-by-provider base-code proliferation.
- The invariant lifecycle keeps platform behavior consistent for all providers.
- The forbidden-leak boundary protects SoC over time.
- Family taxonomy guides tests and rollout order.

## Consequences

**Enables:** scalable provider development, consistent integration checklists, fake lifecycle tests per family, and clear roadmap staging for cloning/dialogue engines.

**Constrains:** provider candidates that are voice-conversion-only, cloning-first, or dialogue-first require product semantics and governance decisions before appearing as normal `/v1/audio/speech` voices.

## Related

- ADR-0013 — VoiceDescriptor discriminated union
- ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity
- ADR-0018 — Provider rollout strategy
- `docs/grills/openai-comp/06-provider-adapter-taxonomy.md`
