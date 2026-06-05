# Define VoiceDescriptor payload union and adapter kind validation

Status: ready-for-agent

## Parent

ADR-0013 — `docs/adr/ADR-0013-voice-descriptor-discriminated-union.md`

## What to build

Define the runtime voice descriptor contract that lets Mery route installed voices to adapters without provider-specific route logic. The slice should make `voiceId -> VoiceDescriptor -> EngineAdapter` type-safe with discriminated payload families and adapter-declared accepted kinds.

## Acceptance criteria

- [ ] Voice descriptors support the approved payload families: preset, model-file, embedding, reference, and designed.
- [ ] Engine adapters declare accepted voice kinds and reject unsupported payload kinds before synthesis.
- [ ] Voice registry resolution can validate that a resolved voice descriptor is compatible with the selected adapter.
- [ ] Fake adapter tests cover at least one accepted and one rejected payload kind.

## Blocked by

None - can start immediately

## Comments
