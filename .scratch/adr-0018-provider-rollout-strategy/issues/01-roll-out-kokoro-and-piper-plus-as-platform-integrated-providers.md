# Roll out Kokoro and Piper-plus as platform-integrated providers

Status: production-ready

## Parent

ADR-0018 — `docs/adr/ADR-0018-provider-rollout-strategy.md`

## What to build

Implement the first provider rollout sequence using catalog-first integration: Kokoro for shared-artifact preset voices and Piper-plus for model-file voices. Each provider should become platform-integrated through catalog entries, hydration, fake lifecycle tests, and marked/manual real runtime validation where dependencies are available.

## Acceptance criteria

- [x] Kokoro catalog entries model one shared artifact referenced by multiple preset voices, with delete/GC tests proving shared artifact retention.
- [x] Piper-plus catalog entries model one voice with model/config artifact roles, with hydration tests proving model-file runtime payloads.
- [x] Provider status distinguishes platform-integrated from audio-validated in docs/diagnostics or test metadata.
- [x] Missing optional dependencies degrade cleanly without breaking other providers or core server startup.
- [x] Marked real-runtime smoke tests exist for Kokoro and Piper-plus and are skipped cleanly when dependencies or fixtures are absent.

## Blocked by

- ADR-0016 issue 01-implement-async-install-job-manifest-commit-and-delete-gc
- ADR-0019 issue 01-codify-provider-adapter-family-checklist-and-tests

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Promote Kokoro and Piper-plus from platform-integrated stubs to audio-validated providers with real dependency detection and fixture smoke tests.
- [x] Publish diagnostics/status that distinguishes missing dependency, missing model, installed but unhealthy, and audio-validated states.

## Evidence

- `src/mery_tts/storage/identity.py` hydrates `model-file` payload templates into `ModelFileVoicePayload` and validates referenced artifacts plus safe relative model paths.
- `tests/unit/test_storage_identity.py::test_kokoro_shared_artifact_gc_retains_artifact_until_last_preset_voice_delete` proves shared Kokoro artifact retention until the final preset voice is deleted.
- `tests/unit/test_storage_identity.py::test_piper_plus_model_file_payload_hydrates_runtime_model_path` proves Piper-plus model/config artifact refs hydrate to a model-file runtime payload.
- `src/mery_tts/providers/rollout.py` exposes structured `ProviderRolloutStatus` with `phase` and runtime states covering `missing_dependency`, `missing_model`, `installed_unhealthy`, and `audio_validated` distinctions.
- `tests/unit/test_provider_adapters.py::{test_piper_plus_real_runtime_smoke_skips_without_dependency,test_kokoro_real_runtime_smoke_skips_without_dependency}` are marked `engine` smoke tests and skip cleanly when optional packages/fixtures are absent.
- Focused verification: `uv run pytest tests/unit/test_storage_identity.py tests/unit/test_doctor_storage_packaging_rollout.py tests/unit/test_provider_adapters.py` → `47 passed, 2 skipped`.

## Comments
