# Grill 04 — Provider rollout strategy

**Parent:** `docs/grills/openai-comp/03-catalog-install-hardening.md`  
**Status:** Q41–Q46 recommended; provider rollout strategy grill closed

This grill designs the provider rollout sequence after:

1. P0 OpenAI-compatible blocking speech.
2. P1 raw PCM HTTP streaming.
3. Catalog/install hardening with fake lifecycle + one real provider entry validation.

The standing constraints for every decision:

- Flexible: provider rollout should support multiple voice/artifact shapes without changing core routes.
- Clean: no provider-specific hacks in OpenAI compatibility, catalog routes, or install routes.
- SoC: adapters, catalog metadata, install pipeline, voice registry, and docs stay separate.
- Modular technically: each provider lands as adapter/catalog/test slices.
- Standalone: each provider can be validated independently.
- Scalable: rollout sequence should teach the platform the main provider shapes before chasing volume.
- Well-tested: fake fixtures first, then marked/manual real-provider validation.

---

## Decision tree

- Q41 Provider rollout order after catalog/install hardening: **Kokoro -> Piper-plus -> Supertonic or VoxCPM2**.
- Q42 Provider rollout sequencing: **catalog-first with fake install lifecycle, then real adapter validation**.
- Q43 Third provider choice: **Supertonic before VoxCPM2 because rollout should prioritize lightweight/no-GPU local-first providers before heavier studio/voice-design engines**.
- Q44 Hardware policy for provider rollout: **priority providers must pass a no-card local-first gate; CUDA-only engines stay later roadmap/P2**.
- Q45 Fallback policy: **no automatic cross-engine fallback in early rollout; exact voice/engine resolution with structured errors and install hints**.
- Q46 Provider rollout DoD: **split provider status into `platform-integrated` and `audio-validated` so fake lifecycle can land before real runtime synthesis is proven**.

---

## Q41 — Provider rollout order after catalog/install hardening

### Recommendation

Roll out providers in this order:

```text
1. Kokoro
2. Piper-plus
3. Supertonic or VoxCPM2
```

This order is not based only on model quality. It is based on which provider shapes best validate Mery’s platform architecture.

### Why Kokoro first

Kokoro should be first because it validates the hardest storage/catalog pattern early:

```text
one shared artifact
-> many preset voices
-> many installed voice manifests
-> one artifact retained while any voice references it
```

That directly stress-tests the catalog/install decisions from Q28–Q40:

- normalized catalog graph;
- artifact IDs separate from voice IDs;
- voice manifests referencing shared artifacts;
- hydration from artifact refs;
- shared-artifact garbage collection;
- OpenAI alias mapping such as `alloy -> kokoro:af_bella`.

If Kokoro works cleanly, Mery proves that providers are not limited to one-file-per-voice. That is important for scaling beyond simple Piper-style voices.

### Why Piper-plus second

Piper-plus should be second because it validates the other essential baseline shape:

```text
one voice
-> model file + config file
-> model-file payload
-> lightweight CPU/offline path
```

It also proves Vietnamese-capable local speech early, which matters for Mery’s target roadmap.

Piper-plus validates:

- `ModelFileVoice` / model-file payload hydration;
- ONNX/config artifact package layout;
- lightweight local install path;
- Vietnamese-capable catalog entries;
- CPU-friendly fallback when heavier engines are unavailable.

### Why Supertonic or VoxCPM2 third

After Kokoro and Piper-plus, Mery has proven shared-preset and model-file baselines. The third provider should validate the strategic 2025–2026 multilingual direction.

Candidate 3A: **Supertonic**

```text
MIT
31 languages incl. Vietnamese
on-device performance story
strong fit for scalable multilingual local TTS
```

Candidate 3B: **VoxCPM2**

```text
Apache 2.0
30 languages incl. Vietnamese
48kHz studio-oriented output
voice design path
strong fit for multilingual + higher-ceiling roadmap
```

Recommendation: choose between Supertonic and VoxCPM2 after checking current package/runtime availability. If both are equally available, prefer **Supertonic first** for likely lighter on-device rollout; use **VoxCPM2 first** if studio-quality Vietnamese and voice design are more important than runtime footprint.

### What not to do

Do not start by adding all providers.

Bad rollout:

```text
add 19 catalog entries
-> discover schemas do not fit
-> discover storage/GC edge cases late
-> tests become slow and provider-dependent
```

Good rollout:

```text
prove one shared-artifact provider
-> prove one model-file provider
-> prove one modern multilingual provider
-> then scale catalog population
```

### Provider rollout unit

Each provider should land as a small vertical slice:

```text
adapter capability descriptor
+ catalog engine/artifact/voice entries
+ payload hydration support
+ fake or tiny fixture tests
+ marked/manual real-provider validation
+ docs entry
```

Do not treat provider rollout as only “add adapter code.” A provider is not integrated until it can move through catalog/install/voice-registry lifecycle.

### Clean module boundary

Provider rollout should not change core route behavior.

Allowed provider-specific code:

```text
src/mery_tts/engines/{provider}/adapter.py
src/mery_tts/engines/{provider}/model_runner.py
provider catalog entries
provider-specific payload hydration branch if needed
provider tests/docs
```

Forbidden provider-specific code:

```text
api/routes/openai_speech.py knows provider names
api/routes/catalog.py knows provider names
api/routes/models.py knows provider names
InstallService branches on provider except through payload/artifact contracts
VoiceRegistry hardcodes provider-specific imports
```

The registry and install system should deal in `engineId`, `artifactRefs`, `payloadTemplate`, and adapter capabilities.

### Test strategy

Minimum rollout tests per provider:

```text
unit/provider_catalog_entry_test.py
  - catalog entries validate against normalized catalog schema
  - artifact refs resolve
  - payload template validates

unit/provider_hydration_test.py
  - installed voice manifest hydrates into runtime VoiceDescriptor
  - required artifact file roles are enforced

contract/provider_install_lifecycle_test.py
  - provider catalog entry can install through fake/temp artifact path
  - installed voice appears in /v1/voices/installed
  - delete removes voice and preserves/removes artifacts correctly

marked/provider_real_engine_test.py
  - real adapter loads when optional dependency is installed
  - real synthesis path works or is manually validated
```

Default CI should not require real engine downloads. Real provider tests stay marked/manual until reliable fixtures exist.

### Decision

Provider rollout order should be:

```text
1. Kokoro       -> validates shared-artifact preset shape
2. Piper-plus   -> validates model-file + Vietnamese-capable lightweight shape
3. Supertonic or VoxCPM2 -> validates modern multilingual/Vietnamese-native strategic direction
```

This keeps rollout flexible, clean, SoC-preserving, modular, standalone per provider, scalable across provider shapes, and well-tested without turning provider population into an uncontrolled big-bang.

---

## Q42 — For each provider, should rollout be adapter-first or catalog-first?

### Recommendation

Use **catalog-first rollout with fake/install lifecycle**, then validate the real adapter.

Recommended order per provider:

```text
1. Add normalized catalog entries.
2. Add or verify payload hydration support.
3. Prove install/delete lifecycle with fake or tiny fixture artifact bytes.
4. Validate real adapter synthesis under marked/manual tests.
```

Provider rollout should not mean “make adapter synthesize once.” It should mean “this provider can participate in Mery’s voice discovery, install, routing, deletion, and diagnostics lifecycle.”

### Why catalog-first

Catalog-first proves the platform path that users and clients actually depend on:

```text
catalog voice card
-> install by catalogEntryId
-> artifact manifest
-> installed voice manifest
-> VoiceRegistry hydration
-> /v1/voices/installed
-> /v1/audio/speech can resolve installed voice
-> delete and GC
```

If the adapter works but the catalog/install path does not, the provider is not product-integrated. It is only a local engine experiment.

### Why not adapter-first

Adapter-first is tempting because it gives fast audio output, but it can hide integration problems:

- no catalog entry shape;
- no artifact identity;
- no payload template;
- no install/delete path;
- no OpenAI alias/install hint story;
- no shared-artifact GC behavior;
- no provider lifecycle tests.

That creates the exact scaling problem Mery is trying to avoid: many engines exist, but each one needs bespoke operational handling.

### Clean rollout unit

Each provider rollout should have two layers:

```text
Layer 1: catalog/install integration
  -> schema entry
  -> artifact refs
  -> payload template
  -> hydration tests
  -> fake lifecycle contract test

Layer 2: real adapter validation
  -> optional dependency import behavior
  -> adapter health
  -> voices() returns descriptors compatible with installed manifests
  -> synthesize() works in marked/manual test
```

The provider is considered platform-integrated after Layer 1. It is considered audio-validated after Layer 2.

### Provider-specific examples

Kokoro catalog-first:

```text
CatalogArtifact: kokoro-v1-onnx
CatalogVoice: kokoro:af_bella -> artifactRefs=[kokoro-v1-onnx], preset template
Fake lifecycle: install fake shared artifact, install af_bella, install another preset, delete one, artifact retained
Real adapter: marked test synthesizes af_bella when kokoro-onnx is installed
```

Piper-plus catalog-first:

```text
CatalogArtifact: piper-plus-vi_VM_meeting-medium-onnx
CatalogVoice: piper-plus:vi_VM_meeting-medium -> model-file template
Fake lifecycle: install fake model/config artifact, hydrate model-file payload
Real adapter: marked test synthesizes Vietnamese fixture when piper-plus is installed
```

Supertonic/VoxCPM2 catalog-first:

```text
CatalogArtifact: model/checkpoint package
CatalogVoice: multilingual default voice or preset -> provider-specific payload template
Fake lifecycle: prove artifact/payload shape first
Real adapter: marked/manual test validates runtime feasibility
```

### Service boundary

Provider catalog rollout should not modify API route logic.

Provider-specific knowledge may live in:

```text
catalog entries
payload template/hydration handlers
engine adapter
engine model runner
provider-specific tests/docs
```

Provider-specific knowledge must not leak into:

```text
/v1/catalog/voices route
/v1/models/install route
/v1/audio/speech route
InstallJobService state machine
ArtifactStore core layout
VoiceStore core manifest logic
```

### Test strategy

Minimum tests per provider rollout:

```text
unit/{provider}_catalog_schema_test.py
  - provider catalog entries validate
  - artifact refs resolve
  - payload template has required roles/fields

unit/{provider}_hydration_test.py
  - provider payload template hydrates to runtime VoiceDescriptor
  - missing required artifact/file role is diagnosed

contract/{provider}_fake_lifecycle_test.py
  - provider voice installs from fake artifact fixture
  - installed voice appears in /v1/voices/installed
  - delete/GC behavior matches provider artifact shape

marked/{provider}_real_adapter_test.py
  - optional dependency missing -> adapter skipped/degraded cleanly
  - optional dependency present -> health/voices/synthesis works
```

Default CI runs catalog/hydration/fake lifecycle tests. Marked real adapter tests run only when dependencies and fixtures are available.

### Decision

Use catalog-first provider rollout:

```text
catalog entry + hydration + fake lifecycle first
real adapter validation second
```

This keeps provider rollout flexible, cleanly separated from routes, modular by provider, standalone from engine availability, scalable across many providers, and well-tested before expensive real-model validation.

---

## Q43 — Third provider choice: Supertonic or VoxCPM2 first?

### Recommendation

Choose **Supertonic before VoxCPM2** for the third provider slot, because the rollout should prioritize the lighter, no-dedicated-GPU path first.

Recommended sequence:

```text
1. Kokoro
2. Piper-plus
3. Supertonic
4. VoxCPM2
```

This keeps Mery aligned with a local-first adoption path: users should be able to get useful multilingual/Vietnamese-native TTS without needing a CUDA card before the platform moves into heavier studio/voice-design engines.

### Why Supertonic first

Supertonic is the better third provider if the goal is lightweight rollout:

```text
Supertonic
  -> MIT
  -> 99M-class model family per roadmap research
  -> 31 languages including Vietnamese
  -> strong on-device performance story
  -> better fit for laptop/local-first Mery installs
```

It validates the strategic 2025–2026 multilingual direction without immediately forcing GPU-heavy deployment assumptions.

The important product signal is:

```text
Mery can support modern multilingual/Vietnamese-native TTS locally, not only classic Piper/Kokoro baselines.
```

### Why VoxCPM2 second

VoxCPM2 is still important, but it should come after the lighter multilingual path.

```text
VoxCPM2
  -> Apache 2.0
  -> 30 languages including Vietnamese
  -> 48kHz studio-oriented output
  -> voice design direction
  -> likely heavier runtime footprint than Supertonic
```

That makes VoxCPM2 a higher-ceiling provider, not the best first multilingual expansion if the user explicitly wants “nhẹ nhàng, ko cần card trước.”

### Rollout principle

Use this provider ordering principle:

```text
baseline quality + easy local path first
-> Vietnamese-capable model-file path second
-> lightweight modern multilingual path third
-> heavier studio/voice-design path fourth
```

Mapped to providers:

```text
Kokoro     -> shared preset artifact, high-quality local English baseline
Piper-plus -> model-file path, Vietnamese-capable lightweight baseline
Supertonic -> lightweight modern multilingual/Vietnamese-native path
VoxCPM2    -> heavier multilingual/studio/voice-design path
```

### Runtime gate

Before committing to Supertonic implementation, run a runtime availability check:

```text
- Is there a usable Python package or ONNX/CoreML/GGUF runtime path?
- Can it run CPU or Apple Silicon without CUDA?
- Are model weights downloadable under MIT-compatible terms?
- Can a tiny smoke test synthesize without a dedicated GPU?
```

If Supertonic fails that gate, do not force it. Fall back to the next lightest no-card option from the roadmap before VoxCPM2.

Fallback preference:

```text
1. Supertonic if no-card runtime is practical
2. Piper/Kokoro expansion if Supertonic packaging is not ready
3. VoxCPM2 only when heavier runtime is acceptable
```

### Catalog-first slice for Supertonic

Supertonic should still follow catalog-first rollout:

```text
CatalogEngine: supertonic
CatalogArtifact: supertonic-lightweight-multilingual-v1
CatalogVoice: supertonic:vi-default or supertonic:multilingual-default
Payload template: provider-specific preset/model package template
Fake lifecycle: install fake Supertonic artifact, hydrate descriptor, delete/GC
Marked real test: synthesize Vietnamese or English sample if runtime is available without GPU
```

Do not start with GPU optimization, full voice list, or all languages. Start with one representative default voice that proves the provider shape.

### Test strategy

Minimum tests for this decision:

```text
unit/supertonic_catalog_schema_test.py
  - Supertonic catalog engine/artifact/voice entries validate
  - payload template validates without GPU-specific fields as required inputs

unit/supertonic_hydration_test.py
  - fake Supertonic installed manifest hydrates to runtime VoiceDescriptor
  - missing artifact/file role is diagnosed

contract/supertonic_fake_lifecycle_test.py
  - fake Supertonic voice installs through catalog/install lifecycle
  - installed voice appears in /v1/voices/installed
  - delete removes voice and GC handles artifact

marked/supertonic_real_runtime_test.py
  - skipped unless runtime package/weights are present
  - verifies no dedicated GPU is required for the smoke path
  - synthesizes a short sample
```

### Decision

Choose **Supertonic as provider #3**, with a runtime feasibility gate that prioritizes no-card local execution.

Keep **VoxCPM2 as provider #4** for the heavier studio/voice-design direction.

This keeps rollout flexible, clean, SoC-preserving, modular by provider, standalone from GPU hardware, scalable toward modern multilingual coverage, and well-tested before committing to heavier engines.

---

## Q44 — Hardware policy for provider rollout: should “no-card first” be a formal gate?

### Recommendation

Yes. Early provider rollout should use a formal **local-first/no-card hardware gate**.

A priority provider must run on at least one of these without requiring a dedicated CUDA GPU:

```text
1. CPU acceptable for short text, or
2. Apple Silicon/CoreML/ANE path, or
3. lightweight ONNX/GGUF runtime without CUDA.
```

CUDA-only providers should stay in later roadmap/P2 until the local-first platform is proven.

### Why this gate matters

Mery’s early value is local TTS that users can actually run on normal machines. If early provider rollout prioritizes GPU-only engines, Mery becomes harder to adopt before the protocol/catalog foundation has matured.

The hardware gate protects the product direction:

```text
works on laptop/local machine first
-> then expands to heavier studio/server engines
```

That matches the user constraint: “nhẹ nhàng, ko cần card trước.”

### Provider classification

Initial classification:

```text
Kokoro
  -> local-first
  -> priority rollout

Piper-plus
  -> local-first
  -> priority rollout

Supertonic
  -> priority if runtime check confirms no-card path

VoxCPM2
  -> later unless no-card runtime is practical
  -> likely heavier studio/voice-design direction

Fish Audio S2
  -> likely GPU/server-first
  -> later roadmap

Higgs Audio v2
  -> GPU ceiling / high VRAM class
  -> later roadmap
```

This is not a quality judgment. It is rollout sequencing based on adoption friction.

### Gate definition

Recommended gate fields in provider evaluation:

```python
class ProviderRuntimeGate(BaseModel):
    provider_id: str
    cpu_supported: bool
    apple_silicon_supported: bool
    onnx_or_gguf_supported: bool
    cuda_required: bool
    min_ram_gb: int | None = None
    min_vram_gb: int | None = None
    smoke_test_available: bool
    priority_rollout_eligible: bool
    notes: str | None = None
```

A provider is priority-eligible when:

```text
priority_rollout_eligible =
  smoke_test_available
  and not cuda_required
  and (cpu_supported or apple_silicon_supported or onnx_or_gguf_supported)
```

### Catalog metadata impact

Catalog entries should eventually expose hardware/runtime metadata, but do not overbuild this first.

Initial catalog/provider metadata can include:

```text
hardware:
  cpu: true/false
  coreml_ane: true/false
  cuda: true/false
  rocm: true/false
  min_ram_gb: optional
  min_vram_gb: optional
```

API projection can later show badges:

```text
CPU
Apple Silicon
CUDA
Large model
No-card friendly
```

But the first provider rollout can keep this as docs/test metadata before making it a full UI/API field.

### Rollout policy

Early rollout policy:

```text
P0/P1 provider rollout:
  must be no-card friendly
  must have fake lifecycle tests
  must have marked/manual real smoke path

P2 provider rollout:
  may require CUDA/server runtime
  must still use the same catalog/install lifecycle
```

This prevents heavy providers from forcing architecture changes. GPU/server providers must plug into the same catalog, artifact, voice manifest, and registry contracts as lightweight ones.

### Supertonic gate

Supertonic should be accepted as provider #3 only if it passes:

```text
- runtime package or model path exists;
- short text synthesis works without CUDA;
- license/weights are compatible with planned use;
- fake lifecycle maps cleanly to catalog/artifact/voice manifests.
```

If Supertonic fails the runtime gate, keep it in roadmap and choose the next lightest no-card provider instead. Do not jump directly to a CUDA-first provider unless the product goal changes.

### Test strategy

Minimum tests/checks for this policy:

```text
unit/provider_runtime_gate_test.py
  - no-card CPU provider is priority eligible
  - Apple Silicon provider is priority eligible
  - CUDA-only provider is not priority eligible for early rollout
  - provider without smoke test is not priority eligible

marked/provider_runtime_smoke_test.py
  - verifies selected provider can synthesize short text without CUDA
  - skips cleanly when optional runtime is missing

catalog/provider_hardware_metadata_test.py
  - provider metadata can represent CPU/CoreML/CUDA capabilities
  - API projection can hide or expose hardware badges without changing install identity
```

### Decision

Make **no-card local-first execution** a formal gate for early provider rollout.

Priority providers must run on CPU, Apple Silicon/CoreML/ANE, or lightweight ONNX/GGUF without CUDA. CUDA-only providers stay later roadmap/P2.

This keeps rollout flexible but disciplined, cleanly separates rollout priority from provider quality, modularizes hardware metadata, stays standalone from any one engine, scales from local-first to server-class engines later, and is well-tested through runtime gate checks and marked smoke tests.

---

## Q45 — Should provider rollout include fallback chains between engines?

### Recommendation

Do **not** include automatic cross-engine fallback in early provider rollout.

Use exact resolution:

```text
requested voiceId
-> exact installed voice
-> exact engine adapter
```

If that voice or engine fails, return a structured error and an install/runtime hint. Do not silently synthesize with another engine.

Default policy:

```text
fallbackPolicy = none
```

### Why automatic fallback is dangerous

Fallback sounds helpful, but TTS engines are not interchangeable.

A fallback can change:

- language;
- accent;
- speaker identity;
- license/commercial-use status;
- voice quality;
- latency;
- audio sample rate;
- emotional tone;
- cloning/consent requirements.

Examples:

```text
Requested: piper-plus:vi_VM_meeting-medium
Fallback: kokoro:af_bella
Problem: Vietnamese request may become English voice behavior.

Requested: supertonic:vi-default
Fallback: piper-plus:vi_VM_meeting-medium
Problem: modern multilingual voice quality/identity changes silently.

Requested: commercial-allowed voice
Fallback: restricted/noncommercial voice
Problem: license behavior changes without caller consent.
```

Silent fallback breaks user trust. The caller asked for a specific voice; Mery should either use that voice or explain why it cannot.

### Clean early behavior

Early provider rollout should use fail-fast exactness:

```text
voice not installed
  -> voice.not_found or model.not_installed
  -> include install hint if catalog knows matching entry

engine missing optional dependency
  -> engine.unavailable
  -> include package install hint

engine health degraded
  -> engine.unavailable or engine.degraded
  -> include diagnostics hint
```

This is more predictable than hidden fallback.

### Install hints instead of fallback

Use helpful errors rather than automatic substitution.

Example native error payload concept:

```json
{
  "error": {
    "code": "voice.not_installed",
    "message": "Voice is not installed: supertonic:vi-default",
    "details": {
      "voiceId": "supertonic:vi-default",
      "catalogEntryId": "supertonic:vi-default@2026-xx",
      "installHint": "POST /v1/models/install with catalogEntryId=supertonic:vi-default@2026-xx"
    }
  }
}
```

OpenAI-compatible routes can translate the same condition into OpenAI-shaped error while preserving useful hint fields where possible.

### Future fallback policy

Fallback can exist later, but only as an explicit policy, never as default magic.

Possible future request/policy field:

```python
class FallbackPolicy(StrEnum):
    NONE = "none"
    SAME_LANGUAGE = "same-language"
    SAME_PROVIDER_FAMILY = "same-provider-family"
    SAME_CAPABILITY_CLASS = "same-capability-class"
```

Default remains:

```text
fallbackPolicy = none
```

Even explicit fallback should obey constraints:

```text
same language/locale if requested
compatible license/commercial_use
compatible payload capability
caller-visible selected voice in response metadata/logs
no fallback for voice cloning unless consent/governance permits
```

### Provider rollout impact

Provider rollout should focus on making each provider independently reliable:

```text
Kokoro installed voice works through Kokoro adapter.
Piper-plus installed voice works through Piper-plus adapter.
Supertonic installed voice works through Supertonic adapter.
```

Do not use fallback to hide incomplete provider integration. If Supertonic adapter is not ready, Supertonic is not audio-validated yet.

### Test strategy

Minimum tests for this decision:

```text
unit/voice_resolution_no_fallback_test.py
  - missing requested voice returns voice.not_found/model.not_installed
  - unavailable requested engine returns engine.unavailable
  - resolver does not choose another installed voice automatically

contract/openai_speech_no_fallback_test.py
  - requested native voiceId is exact
  - OpenAI alias resolves to exact configured voice target
  - missing alias target returns error with install hint, not fallback voice

unit/fallback_policy_future_test.py
  - default policy is none
  - unsupported fallback policy is rejected until implemented
```

### Decision

No automatic cross-engine fallback in early rollout.

Use exact voice/engine resolution with structured errors and install hints. Add explicit fallback policy later only if the product needs it and tests can guarantee language/license/capability safety.

This keeps provider behavior flexible but predictable, cleanly separates resolution from substitution policy, modularizes future fallback, remains standalone per provider, scales without hiding integration failures, and is well-tested through no-fallback contract tests.

---

## Q46 — Provider rollout DoD: when is a provider “integrated”?

### Recommendation

Split provider rollout status into two explicit states:

```text
platform-integrated
audio-validated
```

A provider is **platform-integrated** when its catalog/install/delete/registry lifecycle works with fake artifacts and payload hydration.

A provider is **audio-validated** only when real runtime synthesis passes under marked/manual tests.

This keeps rollout honest: Mery can land provider lifecycle support without pretending the real engine is production-ready before synthesis is actually verified.

### Status definitions

#### `platform-integrated`

A provider reaches `platform-integrated` when:

```text
- normalized catalog engine/artifact/voice entries validate;
- payload templates hydrate into runtime VoiceDescriptor shape;
- fake artifact install passes through /v1/models/install;
- installed voice manifest is written;
- VoiceRegistry.refresh() exposes the voice;
- DELETE /v1/models/{voiceId} removes the voice;
- artifact GC behavior is tested for that provider shape;
- optional dependency missing behavior is cleanly represented as unavailable/skipped.
```

This status proves that the provider fits Mery’s platform architecture.

#### `audio-validated`

A provider reaches `audio-validated` only when:

```text
- optional runtime dependency can be installed;
- adapter health check passes;
- adapter voices() returns descriptors compatible with installed/catalog voices;
- synthesize() produces valid PCMChunk/audio for a short sample;
- marked/manual test records runtime constraints;
- no-card gate passes if the provider is early-rollout priority.
```

This status proves that the provider can actually produce audio in the intended runtime environment.

### Why split the statuses

Without split statuses, teams tend to choose one bad extreme:

```text
Extreme A: block all catalog/platform work until real heavy engine synthesis works.
Extreme B: call provider integrated after only schema/catalog work, even though it cannot synthesize.
```

The split avoids both.

It lets Mery say:

```text
Kokoro platform-integrated, audio-validated
Piper-plus platform-integrated, audio-validated
Supertonic platform-integrated, audio-validation pending runtime gate
VoxCPM2 roadmap, not platform-integrated yet
```

That is clearer than a single overloaded “supported” label.

### API/docs representation

Provider docs and diagnostics should expose status clearly.

Suggested provider rollout table columns:

```text
Provider
Platform lifecycle
Audio runtime
Hardware gate
License
Notes
```

Example:

```text
Kokoro       platform-integrated ✅  audio-validated ✅  no-card ✅
Piper-plus   platform-integrated ✅  audio-validated ✅  no-card ✅
Supertonic   platform-integrated ✅  audio-validated ⏳  no-card gate pending
VoxCPM2      platform-integrated ⏳  audio-validated ⏳  likely heavier
```

Runtime API should avoid overpromising. `/v1/engines` should show only actually available loaded adapters as `available`; catalog docs can separately describe provider rollout status.

### Test requirements

Minimum tests for `platform-integrated`:

```text
unit/{provider}_catalog_schema_test.py
  - catalog entries validate
  - artifact refs resolve

unit/{provider}_hydration_test.py
  - payload template hydrates
  - missing files/artifacts produce diagnostics

contract/{provider}_fake_lifecycle_test.py
  - install fake provider voice
  - voice appears in /v1/voices/installed
  - delete removes voice
  - GC behavior matches provider artifact shape
```

Minimum tests for `audio-validated`:

```text
marked/{provider}_real_adapter_test.py
  - optional dependency missing -> clean skip/degraded status
  - optional dependency present -> health passes
  - voices() returns expected descriptor(s)
  - synthesize(short_text) yields valid PCMChunk/audio
  - runtime/hardware assumptions are recorded
```

Default CI should require `platform-integrated` tests. Marked/manual environments can run `audio-validated` tests.

### Rollout policy

Recommended rollout policy:

```text
A provider may merge as platform-integrated if fake lifecycle tests pass.
A provider may be advertised as usable only after audio-validated passes.
A provider may be priority rollout only if audio-validated also passes the no-card gate.
```

This gives the project velocity without sacrificing honesty.

### Decision

Use two provider rollout statuses:

```text
platform-integrated -> catalog/install/delete/registry lifecycle proven
audio-validated     -> real adapter synthesis proven
```

This keeps rollout flexible, clean in semantics, modular in testing, standalone per provider, scalable across heavy/light engines, and well-tested without blocking platform work on every real runtime.

---

## Provider rollout grill closeout

Final recommended sequence from Q41–Q46:

```text
Q41  Rollout order: Kokoro -> Piper-plus -> Supertonic -> VoxCPM2
Q42  Catalog-first provider rollout, then adapter validation
Q43  Supertonic before VoxCPM2 for lightweight/no-card multilingual path
Q44  Formal no-card local-first hardware gate for priority rollout
Q45  No automatic cross-engine fallback in early rollout
Q46  Provider status split: platform-integrated vs audio-validated
```

Next recommended feature after this grill: **implementation issue breakdown** for the first tracer-bullet sequence:

```text
OpenAI compat P0
-> raw PCM streaming P1
-> catalog/install fake lifecycle
-> Kokoro/Piper-plus/Supertonic provider rollout
```
