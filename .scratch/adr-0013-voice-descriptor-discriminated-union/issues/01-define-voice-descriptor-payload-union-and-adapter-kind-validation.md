# Define VoiceDescriptor payload union and adapter kind validation

Status: production-ready
## Parent

ADR-0013 — `docs/adr/ADR-0013-voice-descriptor-discriminated-union.md`

## What to build

Define the runtime voice descriptor contract that lets Mery route installed voices to adapters without provider-specific route logic. The slice should make `voiceId -> VoiceDescriptor -> EngineAdapter` type-safe with discriminated payload families and adapter-declared accepted kinds.

## Acceptance criteria

- [x] Voice descriptors support the approved payload families: preset, model-file, embedding, reference, and designed. `src/mery_tts/voice/descriptor.py` defines `PresetVoicePayload`, `ModelFileVoicePayload`, `EmbeddingVoicePayload`, `ReferenceVoicePayload`, and `DesignedVoicePayload` as a discriminated union on `kind`.
- [x] Engine adapters declare accepted voice kinds and reject unsupported payload kinds before synthesis. `EngineAdapter.accepted_voice_kinds` and `ensure_voice_supported()` reject unsupported kinds; `tests/unit/test_voice_descriptor.py::test_voice_registry_rejects_adapter_unsupported_payload_kind` pins this.
- [x] Voice registry resolution can validate that a resolved voice descriptor is compatible with the selected adapter. `VoiceRegistry.resolve_for_adapter()` validates compatibility; `tests/unit/test_voice_descriptor.py` covers accepted and rejected resolution.
- [x] Fake adapter tests cover at least one accepted and one rejected payload kind. `tests/unit/test_voice_descriptor.py::test_voice_registry_accepts_adapter_supported_payload_kind` and `test_voice_registry_rejects_adapter_unsupported_payload_kind` cover both paths.

## Blocked by

None - can start immediately

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Validate descriptors loaded from catalog/storage manifests with strict payload-family rules and adapter compatibility before they become routable.
      `StorageIdentityStore._descriptor_from_manifest()` now validates payload family against approved set (`preset`, `model-file`, `embedding`, `reference`, `designed`), rejects unknown families, and validates required fields per family (e.g., `preset_id` for preset). `hydrate_installed_voice_descriptors()` now detects and rejects duplicate voice IDs across manifests.
- [x] Add negative tests for malformed payloads, unsupported families, missing artifacts, duplicate voice IDs, and cross-engine mismatches.
      `tests/unit/test_storage_identity.py` now covers: unsupported payload family rejection, duplicate voice ID rejection, preset payload missing `preset_id` rejection. Existing tests cover missing artifact rejection and unsafe identifier rejection.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Validate descriptors loaded from catalog/storage manifests with strict payload-family rules and adapter compatibility before they become routable.
- Add negative tests for malformed payloads, unsupported families, missing artifacts, duplicate voice IDs, and cross-engine mismatches.
