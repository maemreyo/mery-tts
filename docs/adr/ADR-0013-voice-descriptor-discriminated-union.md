# ADR-0013 — VoiceDescriptor discriminated union

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 01, Q1; Grill 06

## Context

Mery must route synthesis requests to engine adapters using a client-facing `voice_id`, but provider voice data is not uniform. Kokoro-style engines use preset names, Piper-style engines use model/config files, voice conversion engines use embeddings or indexes, cloning engines use reference audio, and voice-design engines may use prompts or speaker configuration.

A flat `VoiceDescriptor` with many optional fields would push unchecked conditionals into adapters and make fake-provider testing brittle.

## Decision

Use a `VoiceDescriptor` whose `payload` is a Pydantic 2 discriminated union over stable voice payload families:

```text
preset
model-file
embedding
reference
designed
```

Each `EngineAdapter` declares `accepted_voice_kinds: frozenset[str]`. `VoiceRegistry` resolves an installed `voice_id` to a hydrated `VoiceDescriptor` and validates that the selected adapter accepts the descriptor payload kind before synthesis.

Adapters receive the full `VoiceDescriptor` and keep provider-specific interpretation inside their own implementation. API routes and catalog/install services do not branch on provider names.

## Rationale

- Discriminated unions make voice routing explicit and type-safe.
- Payload families match the real provider families discovered in the roadmap and adapter taxonomy.
- `accepted_voice_kinds` makes adapter contracts testable with fake descriptors.
- New providers can map to existing payload families without modifying API routes.
- Providers that do not support direct text-to-speech can be kept out of `/v1/audio/speech` until their product semantics are clear.

## Consequences

**Enables:** clean adapter contracts, family-based provider rollout, fake lifecycle tests, and future user-created voice manifests.

**Constrains:** every provider must map catalog/install artifacts to one payload family before it is platform-integrated. If a new provider truly does not fit, a new payload family requires an ADR-level decision rather than ad hoc fields.

## Related

- ADR-0004 — Dual-engine from day one
- ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity
- ADR-0019 — Provider adapter taxonomy
- `docs/grills/openai-comp/01-voice-descriptor-and-engine-selection.md`
- `docs/grills/openai-comp/06-provider-adapter-taxonomy.md`
