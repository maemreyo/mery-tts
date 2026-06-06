# Define VoiceDescriptor payload union and adapter kind validation

Status: scaffold-complete; runtime-follow-up

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

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Validate descriptors loaded from catalog/storage manifests with strict payload-family rules and adapter compatibility before they become routable.
- [ ] Add negative tests for malformed payloads, unsupported families, missing artifacts, duplicate voice IDs, and cross-engine mismatches.
  - Progress: `ModelFileVoicePayload.relative_path` now rejects absolute paths, traversal, backslashes, and Windows drive paths with focused negative tests; unsupported adapter payload-family tests already cover one rejected family. Missing artifacts, duplicate voice IDs, cross-engine mismatches, and catalog/storage manifest validation remain pending.

## Comments
