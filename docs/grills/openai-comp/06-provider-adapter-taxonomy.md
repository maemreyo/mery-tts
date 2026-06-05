# Grill 06 — Provider adapter taxonomy

**Parent:** `docs/grills/openai-comp/01-voice-descriptor-and-engine-selection.md`, `03-catalog-install-hardening.md`, `04-provider-rollout-strategy.md`  
**Status:** consolidated from prior grills; adapter taxonomy baseline

This document consolidates the base/provider-specific architecture decisions from the prior grill chain into one implementation-facing taxonomy.

The goal is to turn “many providers” into a small number of adapter families with clear contracts.

---

## 1. Core principle

Mery should not build one route, install path, or registry path per provider.

Instead:

```text
provider-specific complexity
  -> captured in catalog metadata + payload template + adapter implementation

base platform
  -> remains stable across all providers
```

The invariant:

```text
Catalog entry
-> artifact refs
-> installed voice manifest
-> VoiceRegistry hydration
-> VoiceDescriptor
-> EngineAdapter.synthesize()
```

Every provider must fit this lifecycle before it is considered platform-integrated.

---

## 2. Base platform pieces

These are provider-agnostic and should not contain provider-specific hacks.

### 2.1 `VoiceDescriptor`

Runtime voice object resolved by `VoiceRegistry`.

```python
class VoiceDescriptor(BaseModel):
    voice_id: str
    engine_id: str
    display_name: str
    language: str
    quality_tier: Literal["low", "medium", "high"]
    license: str
    capabilities: list[str]
    payload: VoicePayloadUnion
```

The `payload` is a discriminated union. Provider-specific data must enter through one of these payload families, not through route-level special cases.

Base payload families:

```text
preset
model-file
embedding
reference
designed
```

### 2.2 `EngineAdapter`

Each engine adapter declares what payload kinds it accepts.

```python
class EngineAdapter(ABC):
    @property
    @abstractmethod
    def engine_id(self) -> str: ...

    @property
    @abstractmethod
    def accepted_voice_kinds(self) -> frozenset[str]: ...

    async def health(self) -> EngineHealth: ...

    async def voices(self) -> list[VoiceDescriptor]: ...

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        session_id: str,
    ) -> AsyncIterator[PCMChunk]: ...

    async def cancel(self, session_id: str) -> None: ...
```

Adapter rules:

```text
- no API route imports adapter directly;
- no provider-specific API route branches;
- optional dependency failures degrade cleanly;
- adapter validates accepted payload kind;
- adapter owns engine runtime/model runner lifecycle;
- adapter does not own catalog install logic;
- adapter does not download models directly for normal catalog install flow.
```

### 2.3 Normalized catalog

Signed/trusted catalog is normalized internally:

```text
CatalogDocument
  engines[]
  artifacts[]
  voices[]
```

External API exposes flat cards:

```text
GET /v1/catalog/voices -> CatalogVoiceCard[]
```

### 2.4 Installed manifests

Stored bytes and routable voices are separate.

```text
artifacts/{engineId}/{artifactId}/artifact.json
voices/{safeVoiceId}.json
```

Identity split:

```text
catalogEntryId -> installable catalog item identity
artifactId     -> stored bytes/package identity
voiceId        -> installed/routable voice identity
engineId       -> adapter identity
```

### 2.5 Hydration

Installed voice manifests persist logical references, not brittle runtime paths.

```text
voiceId + engineId + artifactRefs[] + payloadTemplate
```

`VoiceRegistry.refresh()` hydrates runtime descriptors:

```text
VoiceStore.list()
-> ArtifactStore.resolve(artifactRefs)
-> hydration handler builds VoiceDescriptor.payload
-> registry copy-on-write swap
```

---

## 3. Provider adapter families

Most providers should fit one of these families.

### Family A — Preset/shared-artifact adapters

Use when many voices are presets inside one shared model/artifact.

Canonical examples:

```text
Kokoro
Supertonic, if runtime exposes preset/speaker IDs
possibly Dia/Orpheus if wrapped as preset speakers later
```

Shape:

```text
one shared artifact
-> many CatalogVoice entries
-> many InstalledVoiceManifest files
-> one retained artifact while any voice references it
```

Catalog shape:

```text
CatalogArtifact
  artifactId: kokoro-v1-onnx
  engineId: kokoro
  files: model.onnx, voices.bin/config

CatalogVoice
  catalogEntryId: kokoro:af_bella@kokoro-v1
  voiceId: kokoro:af_bella
  engineId: kokoro
  artifactRefs: [kokoro-v1-onnx]
  payloadTemplate.kind: preset-template
  payloadTemplate.presetName: af_bella
```

Hydrated runtime payload:

```python
class PresetVoice(BaseModel):
    kind: Literal["preset"]
    preset_name: str
    # optional hydrated model/voices paths if adapter needs them
```

Adapter development basis:

```text
- load shared model once in model runner;
- map preset_name to provider voice/speaker ID;
- synthesize text with selected preset;
- cancel by session_id if runtime supports cooperative cancellation;
- expose many voices from one artifact.
```

Tests:

```text
- two voices share same artifact;
- deleting one voice retains artifact;
- deleting last voice removes artifact;
- missing preset is diagnosed;
- adapter missing optional dependency is skipped/degraded.
```

---

### Family B — Model-file voice adapters

Use when one voice is primarily one model/config package.

Canonical examples:

```text
Piper-plus
MeloTTS-Vietnamese, if packaged as local model/config
possibly RVC base model in some modes
```

Shape:

```text
one voice
-> one model artifact package
-> model file + config file
-> model-file payload
```

Catalog shape:

```text
CatalogArtifact
  artifactId: piper-plus-vi_VM_meeting-medium-onnx-2026-06
  engineId: piper-plus
  files: model.onnx, config.json

CatalogVoice
  catalogEntryId: piper-plus:vi_VM_meeting-medium@2026-06
  voiceId: piper-plus:vi_VM_meeting-medium
  engineId: piper-plus
  artifactRefs: [piper-plus-vi_VM_meeting-medium-onnx-2026-06]
  payloadTemplate.kind: model-file-template
  payloadTemplate.modelFileRole: model
  payloadTemplate.configFileRole: config
```

Hydrated runtime payload:

```python
class ModelFileVoice(BaseModel):
    kind: Literal["model-file"]
    model_path: str
    config_path: str | None = None
```

Adapter development basis:

```text
- load model/config from hydrated paths;
- model runner owns warmup/threadpool/runtime object;
- synthesize text to PCM chunks;
- keep dependency optional;
- do not assume every voice has separate code path.
```

Tests:

```text
- model/config file roles required;
- missing config diagnosed if required by engine;
- fake model-file lifecycle installs and hydrates;
- real marked smoke test synthesizes short sample when dependency/model exists.
```

---

### Family C — Embedding / voice-conversion adapters

Use when voice identity depends on embedding/index/checkpoint artifacts rather than a simple preset or model file.

Canonical examples:

```text
OpenVoice v2
RVC
some speaker embedding systems
```

Shape:

```text
base converter/runtime artifact
+ embedding/index/checkpoint artifact
-> embedding payload
```

Catalog shape may be one of:

```text
one CatalogVoice -> one embedding artifact
one CatalogVoice -> base artifact + embedding artifact
many voices -> shared base artifact + distinct embeddings
```

Hydrated runtime payload:

```python
class EmbeddingVoice(BaseModel):
    kind: Literal["embedding"]
    embedding_path: str
    index_path: str | None = None
    base_model_path: str | None = None
```

Adapter development basis:

```text
- adapter accepts embedding payload;
- model runner loads base model once when possible;
- per-voice embedding/index selected at synth/convert time;
- if provider is VC-only, API may require source audio in future route, so do not force it into /v1/audio/speech until product semantics are clear.
```

Important constraint:

```text
If engine is voice-conversion-only, do not pretend it is normal text-to-speech unless it actually can synthesize from text.
```

Tests:

```text
- shared base artifact retained while embeddings reference it;
- missing embedding/index diagnosed;
- catalog entry clearly marks capability as voice_conversion if not direct TTS;
- no OpenAI speech path unless direct text-to-speech is supported.
```

---

### Family D — Reference / zero-shot cloning adapters

Use when voice identity is derived from reference audio, transcript, or speaker prompt at runtime/install time.

Canonical examples:

```text
XTTS-v2
F5-TTS
Chatterbox
NeuTTS Air
Qwen3-TTS, if used for prompt/reference cloning
```

Shape:

```text
base model artifact
+ reference audio/transcript metadata
+ consent/governance metadata
-> reference payload
```

Hydrated runtime payload:

```python
class ReferenceVoice(BaseModel):
    kind: Literal["reference"]
    audio_path: str
    transcript: str
    duration_seconds: float
    consent_id: str | None = None
```

Adapter development basis:

```text
- adapter validates reference payload;
- model runner loads base model;
- synthesize uses reference audio/transcript according to provider requirements;
- cloning/consent rules must be enforced before creating installed voice manifest;
- do not make cloning a silent catalog install without governance.
```

Governance gate:

```text
Reference voices require consent/provenance design before being first-class user-created voices.
```

Tests:

```text
- missing transcript rejected when provider requires transcript;
- missing consent_id rejected once governance gate is enabled;
- reference audio artifact/path hydration works;
- OpenAI route does not bypass cloning governance.
```

---

### Family E — Designed / prompt-driven voice adapters

Use when provider supports voice design by text prompt, speaker description, style prompt, multi-speaker dialogue config, or similar provider-native controls.

Canonical examples:

```text
VoxCPM2
Orpheus
Dia
some future voice-design engines
```

Shape:

```text
base model/checkpoint artifacts
+ design prompt / speaker config
-> designed payload
```

Hydrated runtime payload:

```python
class DesignedVoice(BaseModel):
    kind: Literal["designed"]
    design_prompt: str
    reference_audio_path: str | None = None
    speaker_config: dict[str, str] | None = None
```

Adapter development basis:

```text
- adapter accepts designed payload;
- provider-specific prompt/config interpretation stays inside adapter;
- catalog may ship default designed voices/presets;
- user-created designed voices need separate governance/storage workflow later;
- avoid exposing arbitrary provider knobs in base API.
```

Tests:

```text
- designed payload hydrates from manifest;
- provider-specific config remains adapter-local;
- missing base checkpoint/tokenizer/config is diagnosed;
- heavy/GPU runtime is marked later roadmap unless no-card gate passes.
```

---

### Family F — Dialogue / multi-speaker adapters

Use when engine is optimized for multi-speaker dialogue rather than single-voice TTS.

Canonical examples:

```text
Dia
possibly Orpheus-style conversational engines
```

This family may overlap with designed/prompt adapters, but product semantics are different.

Base `/v1/audio/speech` is single-output speech. Multi-speaker dialogue may need later API shape.

Development rule:

```text
Do not force multi-speaker dialogue engines into the single-voice API unless there is a clean default single-speaker mode.
```

Possible future route:

```text
POST /v1/audio/dialogue
```

Until then, these engines can remain roadmap or expose only a constrained single-speaker preset mode.

---

## 4. What every provider must provide

Each provider rollout needs these pieces.

### 4.1 Adapter package slice

```text
src/mery_tts/engines/{provider}/adapter.py
src/mery_tts/engines/{provider}/model_runner.py
pyproject optional dependency extra
entry point registration
```

Adapter must prove:

```text
- import failure is isolated;
- health reports available/degraded/unavailable;
- accepted_voice_kinds is correct;
- synthesize accepts hydrated VoiceDescriptor;
- cancel(session_id) is idempotent;
- real tests are marked/manual if model dependency is heavy.
```

### 4.2 Catalog slice

```text
CatalogEngine
CatalogArtifact(s)
CatalogVoice(s)
payloadTemplate
hardware metadata when known
license/commercial_use
source/provenance
```

### 4.3 Hydration slice

Provider or family hydration must map:

```text
InstalledVoiceManifest.payloadTemplate
+ ArtifactStore resolved files
-> runtime VoiceDescriptor.payload
```

Hydration failures must diagnose and skip broken voice, not crash all registry refresh.

### 4.4 Fake lifecycle slice

Each provider family should have fake artifact tests:

```text
catalog entry validates
install fake artifact
write artifact manifest
write voice manifest
refresh registry
voice appears installed
DELETE voice
GC behavior correct
```

### 4.5 Real runtime slice

Marked/manual tests:

```text
optional dependency present
adapter health passes
voices() returns descriptors
synthesize(short_text) emits PCMChunk/audio
hardware assumptions recorded
```

---

## 5. Base vs provider-specific boundary

### Base platform owns

```text
/v1/audio/speech route
/v1/catalog/voices route
/v1/models/install route
/v1/voices/installed route
/v1/engines route
EngineRegistry discovery
VoiceRegistry routing/refresh
CatalogRepository
InstallJobService
ArtifactStore
VoiceStore
ArtifactGarbageCollector
OpenAI-compatible error mapping
Web console API consumption
```

### Provider-specific code owns

```text
engine adapter
model runner
runtime dependency handling
provider-specific payload interpretation
provider-specific hydration helper if needed
provider catalog entries
provider marked tests
provider docs/runtime notes
```

### Forbidden leaks

Do not put provider-specific logic in:

```text
api/routes/openai_speech.py
api/routes/catalog.py
api/routes/models.py
api/routes/voices.py
InstallJobService state machine
ArtifactStore core path layout
VoiceStore core manifest format
OpenAI alias resolver beyond data config
Web console feature logic beyond displaying metadata
```

---

## 6. Provider development checklist

For any new provider, answer these before coding:

```text
1. Which adapter family is it?
   preset / model-file / embedding / reference / designed / dialogue

2. Does it support direct text-to-speech?
   If no, do not expose through /v1/audio/speech yet.

3. What artifacts does it need?
   model, config, tokenizer, voice-pack, embedding, reference audio, index

4. Is artifact sharing expected?
   one artifact -> many voices, one voice -> many artifacts, or one-to-one

5. What payload template should catalog install persist?

6. What runtime payload should VoiceRegistry hydrate?

7. Does it pass no-card local-first gate?
   CPU / Apple Silicon / ONNX / GGUF without CUDA

8. What license/commercial-use metadata applies?

9. What fake lifecycle test proves platform integration?

10. What marked/manual real test proves audio validation?
```

Provider is not done until it has at least:

```text
platform-integrated -> fake lifecycle passes
audio-validated     -> real synthesis passes
```

---

## 7. Current recommended rollout mapping

```text
1. Kokoro
   family: preset/shared-artifact
   validates: shared artifact, preset voices, GC retention
   status target: platform-integrated + audio-validated

2. Piper-plus
   family: model-file
   validates: model/config package, Vietnamese-capable lightweight path
   status target: platform-integrated + audio-validated

3. Supertonic
   family: likely preset/shared-artifact or lightweight model package
   validates: modern multilingual no-card path if runtime check passes
   status target: platform-integrated first, audio-validated after no-card smoke

4. VoxCPM2
   family: designed/prompt or model package
   validates: heavier studio/voice-design direction
   status target: later, after local-first providers
```

Other roadmap candidates by likely family:

```text
XTTS-v2        -> reference / zero-shot cloning
F5-TTS         -> reference / zero-shot cloning
OpenVoice v2   -> embedding / voice conversion
Fish Audio S2  -> heavier multilingual/server-first, likely later
CosyVoice 2    -> reference/preset hybrid depending integration path
MeloTTS-VI     -> model-file
ChatTTS        -> rejected by license
RVC            -> embedding / voice conversion
Chatterbox     -> reference / emotion-capable
Orpheus        -> designed/prompt or dialogue
Dia            -> dialogue / multi-speaker
Higgs Audio v2 -> heavy/server-first, later
Qwen3-TTS      -> reference/preset depending package
NeuTTS Air     -> reference or preset with GGUF artifact
```

---

## 8. Decision

Mery’s provider strategy should be based on adapter families, not individual provider hacks.

Base platform remains stable:

```text
VoiceDescriptor
+ EngineAdapter
+ normalized catalog
+ artifact store
+ installed voice manifest
+ hydration
+ VoiceRegistry
+ install/delete lifecycle
```

Provider-specific work plugs into one of the adapter families:

```text
preset
model-file
embedding
reference
designed
dialogue
```

This keeps the system flexible for many providers, clean in SoC boundaries, modular per adapter family, standalone per provider rollout, scalable beyond the first 19 providers, and well-tested through fake lifecycle plus marked real runtime validation.
