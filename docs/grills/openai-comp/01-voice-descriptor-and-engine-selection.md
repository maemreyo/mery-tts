# Grill 01 — Voice Descriptor + Engine Selection (P0 Protocol w/ 19 Providers)

**Date:** 2026-06-05
**Status:** Q1–Q19 recommended, awaiting user confirmation
**Trigger:** P0 Protocol deployment when 19 engine providers exist; OpenAI compat as distribution hack
**Source context:** `docs/reports/roadmap-research/99-priority-matrix.md` (P0 #2 — OpenAI compat)
**Decision tree position:** Foundation level (no dependencies upstream)

---

## Decision tree so far

- **Q1** — `voiceId` trỏ tới cái gì? (foundation)
- **Q2** — Engine selection policy: client chọn engine bằng cách nào?
- **Q3** — OpenAI voice alias mapping config: `alloy` → Mery native `voice_id`
- **Q4** — `/v1/engines` response schema: minimal status vs. capability matrix
- **Q5** — Catalog voice model: installable voice vs. engine/model graph
- **Q6** — Engine weight/model storage: artifact store + voice manifests
- **Q7** — `/v1/audio/speech` response delivery mode: blocking MVP, chunked streaming P1
- **Q8** — OpenAI-compatible error mapping: route-specific adapter over native errors
- **Q9** — Auth model for OpenAI compat: reuse Mery token for MVP, optional compat keys in P1
- **Q10** — Endpoint path strategy: expose OpenAI-compatible `/v1/audio/speech` directly
- **Q11** — Compatibility scope: OpenAI-like schema with explicit unsupported errors
- **Q12** — Integration test strategy: unit + FastAPI contract + OpenAI SDK smoke with fake adapter
- **Q13** — Implementation slicing: vertical tracer bullet, not route-first hack or foundation big-bang
- **Q14** — P0 definition of done: real-engine done with one lightweight engine behind the OpenAI path
- **Q15** — First real engine gate: dual-engine P0 with Piper-plus + Kokoro
- **Q16** — Runtime dependency handling: core-only server starts; missing engines degrade cleanly
- **Q17** — Alias target availability: deterministic alias metadata + install hints, no auto-install
- **Q18** — User documentation location: dedicated integration doc plus README link
- **Q19** — Next feature after P0: chunked HTTP streaming for `/v1/audio/speech`
- Q20+ — TBD as we walk down

---

## Q1 — Voice descriptor: Pydantic 2 discriminated union (Option B, refined)

**Verdict:** VoiceId resolves to a `VoiceDescriptor` whose `payload` is a discriminated union over 5 kinds (preset, model-file, embedding, reference, designed). Each engine adapter declares `accepted_voice_kinds`. Adapter uses structural pattern matching internally.

**Why B over A / C / D:**

| Option | Verdict | Reason rejected |
|---|---|---|
| A — universal ref audio | ❌ | Forces Kokoro preset → ref audio round-trip; loses semantic; storage waste |
| **B — polymorphic + discriminator** | ✅ | Idiomatic Pydantic 2 sum type; engine keeps native form; type-safe |
| C — opaque string + manifest JSON | ❌ | No type safety; adapters do `if "audio" in manifest` spaghetti |
| D — hybrid bundled vs user | ❌ | Two namespaces = two code paths; discriminator already separates them cleanly |

**Schema sketch** (`src/mery_tts/schemas/v1/voices.py`):

```python
from pydantic import BaseModel, Field
from typing import Literal, Union

class VoicePayload(BaseModel):
    kind: str  # discriminator — never instantiated directly

class PresetVoice(VoicePayload):
    """Kokoro 'af_bella', Supertonic 'speaker_0', VoxCPM2 preset"""
    kind: Literal["preset"]
    preset_name: str

class ModelFileVoice(VoicePayload):
    """Piper-plus onnx, RVC .pth — voice IS the model"""
    kind: Literal["model-file"]
    model_path: str
    config_path: str | None = None

class EmbeddingVoice(VoicePayload):
    """OpenVoice v2, RVC index"""
    kind: Literal["embedding"]
    embedding_path: str

class ReferenceVoice(VoicePayload):
    """Chatterbox, NeuTTS Air, Qwen3-TTS clone, XTTS-v2 zero-shot"""
    kind: Literal["reference"]
    audio_path: str
    transcript: str          # mandatory for clone
    duration_seconds: float
    consent_id: str | None = None  # governance trail (recommended for clones)

class DesignedVoice(VoicePayload):
    """VoxCPM2 voice design, Orpheus emotion prompt"""
    kind: Literal["designed"]
    design_prompt: str
    reference_audio_path: str | None = None

VoicePayloadUnion = Union[
    PresetVoice, ModelFileVoice, EmbeddingVoice, ReferenceVoice, DesignedVoice
]

class VoiceDescriptor(BaseModel):
    voice_id: str            # "{engine_id}:{native_name}" — e.g. "kokoro:af_bella"
    engine_id: str
    display_name: str
    language: str            # BCP-47
    quality_tier: Literal["low", "medium", "high"]
    license: str             # SPDX
    size_bytes: int | None = None
    sample_url: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    payload: VoicePayloadUnion = Field(discriminator="kind")
```

**Adapter contract change** (`src/mery_tts/engines/base.py`):

```python
class EngineAdapter(ABC):
    @property
    @abstractmethod
    def accepted_voice_kinds(self) -> frozenset[str]:
        """Whitelist of VoicePayload.kind values this adapter can route."""

    @abstractmethod
    async def voices(self) -> list[VoiceDescriptor]: ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,         # full descriptor, not just ID
        session_id: str,
    ) -> AsyncIterator[PCMChunk]: ...

    @abstractmethod
    async def cancel(self, session_id: str) -> None: ...
```

**VoiceRegistry routing** (`src/mery_tts/engines/voice_registry.py`):

```python
def resolve(self, voice_id: str) -> tuple[EngineAdapter, VoiceDescriptor]:
    descriptor = self._routing[voice_id]
    adapter = self._engine_registry.get(descriptor.engine_id)
    if descriptor.payload.kind not in adapter.accepted_voice_kinds:
        raise VoiceKindMismatch(voice_id, descriptor.payload.kind, adapter.engine_id)
    return adapter, descriptor
```

**Adapter internal dispatch** (Python 3.12 structural match):

```python
# inside KokoroAdapter.synthesize
match voice.payload:
    case PresetVoice(preset_name=name):       return self._synth_preset(text, name, session_id)
    case ModelFileVoice(model_path=path):     return self._synth_model(text, path, session_id)
    case _: raise VoiceKindMismatch(...)  # shouldn't reach — registry filters
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/schemas/v1/voices.py` | NEW — 5 VoicePayload subclasses + VoiceDescriptor |
| `src/mery_tts/engines/base.py` | Extend ABC: add `accepted_voice_kinds`, change `synthesize(voice_id)` → `synthesize(voice)` |
| `src/mery_tts/engines/voice_registry.py` | Validate kind compatibility on resolve |
| `src/mery_tts/engines/piper_plus/adapter.py` | Declare `accepted_voice_kinds={"model-file"}`; emit ModelFileVoice |
| `src/mery_tts/engines/kokoro/adapter.py` | Declare `{"preset"}`; emit PresetVoice |
| Future 17 adapters | Each declares its own kind whitelist + emits matching payload |

**Test pyramid:**

```python
# tests/contract/voices/test_kinds.py
def test_preset_voice_round_trip():
    v = VoiceDescriptor(engine_id="kokoro", voice_id="kokoro:af_bella",
        display_name="Bella", language="en-US", quality_tier="high",
        license="Apache-2.0", payload=PresetVoice(kind="preset", preset_name="af_bella"))
    assert VoiceDescriptor.model_validate_json(v.model_dump_json()) == v

def test_wrong_kind_rejected():
    with pytest.raises(ValidationError):
        ReferenceVoice(kind="preset", audio_path="x", transcript="t", duration_seconds=1.0)

# tests/contract/adapters/test_kokoro_adapter.py
async def test_kokoro_accepts_only_preset_and_model_file():
    assert kokoro.accepted_voice_kinds == frozenset({"preset", "model-file"})

async def test_kokoro_rejects_reference_voice():
    with pytest.raises(VoiceKindMismatch):
        await kokoro.synthesize("hi", reference_descriptor, "sess-1")

# tests/unit/voice_registry/test_routing.py
def test_routing_is_copy_on_write():
    reg = VoiceRegistry(fake_registry_with([preset_a, preset_b]))
    snapshot = reg._routing
    reg.refresh()
    assert reg._routing is not snapshot
```

---

## Q2 — Engine selection policy: lightest path

**Verdict:** (a) auto-resolve from `voice_id` — no engine param needed in default flow. (b) OpenAI `model` field for explicit override. (c) No fallback at MVP — fail fast with `engine.unavailable`.

### (a) Default selection when client doesn't specify engine

**Verdict:** `VoiceRegistry` routes by `voice_id` alone. Client never needs to know engine.

- `voice_id` is already namespaced by engine (`kokoro:af_bella`, `piper-plus:en_US-lessac-medium`)
- Mery resolves `voice_id` → `(adapter, descriptor)` in 1 lookup
- Zero config, zero decision, zero choice paralysis
- OpenAI voices (`alloy`, `echo`, …) → 400 with `voice.not_found` at MVP; P1 adds alias config file

### (b) Where explicit engine selection lives

**Verdict:** Reuse OpenAI's `model` field. Body-only. No header, no query param.

OpenAI request shape → Mery mapping:

```json
POST /v1/audio/speech
{
  "model": "tts-1",        // OpenAI: tts-1 | tts-1-hd | gpt-4o-mini-tts
                            // Mery:   any of: "<engine_id>" | "mery/<engine_id>"
                            //         or omit entirely (auto-resolve from voice)
  "input": "Hello",
  "voice": "alloy"         // OpenAI: alloy | echo | fable | onyx | nova | shimmer
                            // Mery:   any installed voice_id, or OpenAI alias (P1)
}
```

- Backward compatible — extra fields ignored by OpenAI SDK; OpenAI clients fail predictably
- No URL pollution (`?engine=voxbox-cpm2` complicates caching, logging)
- No header auth complexity (token already in `Authorization`)
- Easy to unit-test (body is JSON, no header parsing)

Validation rules:

```python
def resolve_model(model: str | None, voice_id: str) -> EngineId | None:
    """Returns engine_id if model forces one; None = auto-resolve from voice_id."""
    if model is None:
        return None  # auto-resolve
    if model.startswith("mery/"):
        return model.removeprefix("mery/")
    if model in engine_registry.all_ids():
        return model
    if model in OPENAI_LEGACY_ALIASES:  # tts-1, tts-1-hd → defaults
        return settings.openai_legacy_default  # e.g. "kokoro"
    raise InvalidModelError(model)
```

### (c) Fallback when selected engine fails

**Verdict:** No fallback at MVP. Fail fast with `engine.unavailable`.

- Most lightweight: client knows which engine it picked, so client can decide
- Avoids silent quality degradation (user wants VoxCPM2, gets piper-plus)
- Avoids config explosion (19 engines × fallback permutations = combinatorial)
- Mitigation: `EngineRegistry` already skips failed loads (ADR-0004); `mery doctor` flags health; P1 can add `X-Mery-Fallback-Chain: piper-plus,kokoro` header

### Trade-offs accepted

| Decision | Trade-off | Mitigation |
|---|---|---|
| Auto-resolve from voice_id | Client can't say "use ANY engine that supports VI at 24kHz" | `GET /v1/voices/installed?language=vi` filters by capability; client picks |
| Reuse `model` field for engine | Non-standard — OpenAI uses `model` for version, not engine | Accept any string; validate against installed engines; 400 on unknown |
| No fallback | Less resilient | EngineRegistry skips failed loads; `mery doctor`; P1 header for opt-in fallback |

---

## Q3 — OpenAI voice alias mapping config

**Verdict:** Use a dedicated `OpenAIVoiceAliasResolver` backed by deterministic config. Do not hardcode aliases inside routes. Do not dynamically pick "best installed voice" at MVP.

**Recommended shape:**

```text
src/mery_tts/openai_compat/
  __init__.py
  aliases.py        # OpenAIVoiceAliasResolver
  schemas.py        # OpenAI-compatible request/response schemas
```

Bundled default config:

```text
src/mery_tts/catalog/bundled/openai-voice-aliases-v1.json
```

```json
{
  "schemaVersion": "1.0",
  "aliases": {
    "alloy": "kokoro:af_bella",
    "echo": "kokoro:am_adam",
    "fable": "piper-plus:en_US-lessac-medium",
    "onyx": "kokoro:am_michael",
    "nova": "kokoro:af_nicole",
    "shimmer": "kokoro:af_sarah"
  }
}
```

Resolution order:

```text
user override aliases > bundled default aliases > raw native voice_id fallback > voice.not_found
```

Runtime flow:

```text
POST /v1/audio/speech { model: "tts-1", voice: "alloy", input: "..." }
  -> OpenAISpeechRequest validates OpenAI-compatible shape
  -> OpenAIVoiceAliasResolver.resolve("alloy")
  -> "kokoro:af_bella"
  -> VoiceRegistry.resolve("kokoro:af_bella")
  -> KokoroAdapter.synthesize(...)
```

**Why this is the clean recommendation:**

| Criterion | Why C wins |
|---|---|
| Flexible | User can remap aliases to Kokoro, Piper-plus, VoxCPM2, etc. without code changes |
| Clean | Route calls `alias_resolver.resolve()` and stays transport-oriented |
| SoC | `openai_compat/aliases.py` owns OpenAI aliasing; `VoiceRegistry` owns native routing; adapters own synthesis |
| Modular | OpenAI compatibility is an adapter layer over native `/v1`, not a forked engine path |
| Standalone | Bundled config works offline with no Zam Reader, no network, no remote catalog |
| Scalable | More aliases or locale-specific aliases are data-only changes |
| Well-tested | Unit-test resolver with fake config; route contract-test with fake VoiceRegistry; no real engine required |

**Guardrail:** Alias resolution must be deterministic. Do not implement dynamic best-voice magic at MVP because `alloy -> sometimes kokoro, sometimes piper-plus, sometimes voxcpm2` destroys reproducibility and makes bug reports hard.

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/openai_compat/aliases.py` | NEW — config loader + deterministic alias resolver |
| `src/mery_tts/openai_compat/schemas.py` | NEW — OpenAI-compatible speech request/response schemas |
| `src/mery_tts/catalog/bundled/openai-voice-aliases-v1.json` | NEW — bundled default aliases |
| `src/mery_tts/api/routes/openai_speech.py` | NEW or route extension — calls resolver then VoiceRegistry |
| `tests/unit/openai_compat/test_aliases.py` | NEW — precedence, fallback, invalid config |
| `tests/contract/api/test_openai_speech.py` | NEW — `alloy` alias, native voice_id fallback, unknown voice error |

---

## Q4 — `/v1/engines` response schema

**Verdict:** Expose a full but stable **capability matrix**, not just `engineId/status`. Keep it runtime-read-only and descriptor-only: no model paths, no secrets, no backend internals that clients can depend on accidentally.

**Recommended endpoint:**

```text
GET /v1/engines
```

**Response sketch:**

```python
class EngineCapabilitySet(BaseModel):
    voice_kinds: list[Literal["preset", "model-file", "embedding", "reference", "designed"]]
    languages: list[str]                 # BCP-47-ish normalized, e.g. ["en-US", "vi-VN"]
    streaming: bool
    ttfb_streaming: bool
    word_timing: bool
    ssml: bool
    voice_cloning: bool
    voice_design: bool
    emotion_control: bool

class EngineHardwareSupport(BaseModel):
    cpu: bool
    coreml_ane: bool
    cuda: bool
    rocm: bool
    webgpu: bool
    active_backend: Literal["cpu", "coreml_ane", "cuda", "rocm", "webgpu", "unknown"]

class EngineDescriptor(BaseModel):
    engine_id: str                       # "kokoro"
    display_name: str                    # "Kokoro"
    provider: str                        # "hexgrad" / "zaob-dev" / "OpenBMB"
    adapter_version: str                 # package adapter version, not model version
    status: Literal["available", "degraded", "unavailable"]
    status_reason: str | None = None     # stable machine-readable reason
    license: str                         # SPDX expression
    commercial_use: Literal["allowed", "restricted", "unknown"]
    installed_voice_count: int
    capabilities: EngineCapabilitySet
    hardware: EngineHardwareSupport
```

**API response:**

```python
class EnginesResponse(BaseModel):
    schema_version: Literal["1.0"]
    engines: list[EngineDescriptor]
```

**Why full capability matrix, not minimal status:**

| Criterion | Why full descriptor wins |
|---|---|
| Flexible | Clients can filter by language, voice cloning, streaming, backend without new endpoints |
| Clean | Engine metadata is centralized in one response instead of scattered through docs/UI rules |
| SoC | `EngineRegistry` collects adapter descriptors; API only serializes response; adapters own their own capabilities |
| Modular | New engine only implements `descriptor()` / capability fields; route stays unchanged |
| Standalone | `mery engines list`, `/v1/engines`, diagnostics, and tests can use the same descriptor object |
| Scalable | 19 engines become data rows, not special-case code paths |
| Well-tested | Fake adapters return descriptors; contract tests assert schema shape and filtering behavior without real engines |

**Important boundary:** `/v1/engines` describes **engine capability**, not installed model inventory. Installed voices remain under `/v1/voices/installed`; downloadable voices remain under `/v1/catalog/voices`. Do not merge those concerns.

```text
/v1/engines          -> what adapters are available and what they can do
/v1/voices/installed -> what voices are locally usable now
/v1/catalog/voices   -> what voices/models can be installed
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/schemas/v1/engines.py` | NEW/extend — EngineDescriptor + capability/hardware structs |
| `src/mery_tts/engines/base.py` | Add `descriptor()` or `capabilities` property to EngineAdapter |
| `src/mery_tts/engines/registry.py` | Collect descriptors, health/status, active backend |
| `src/mery_tts/api/routes/engines.py` | Return `EnginesResponse` from registry descriptors |
| `tests/unit/engines/test_engine_descriptor.py` | Schema validation, status reason, hardware defaults |
| `tests/contract/api/test_engines_endpoint.py` | Response shape with fake adapters, unavailable/degraded cases |

**Testing requirements:**

```text
1. Descriptor schema round-trip: EngineDescriptor.model_validate_json(...)
2. Fake available adapter appears with status=available
3. Fake adapter that raises during health appears as status=unavailable OR is skipped per ADR-0004 policy; choose one behavior explicitly
4. Capabilities are stable and do not depend on installed voices
5. Installed voice count changes after VoiceRegistry refresh, but engine capability fields do not
6. `/v1/engines` must not expose local filesystem paths or model file names
```

**Recommendation nuance:** ADR-0004 currently says failed load → warning + skipped. For `/v1/engines`, keep that policy for import-time failures. Only adapters that load successfully but fail health should appear as `degraded` or `unavailable`. This preserves startup resilience while still making runtime health inspectable.

---

## Q5 — Catalog voice model

**Verdict:** For P0, catalog unit should be **installable voice**. Do not start with full `engines[] + models[] + voices[]` graph. Keep catalog entries user-facing, directly installable, and route-ready after install.

The important distinction:

```text
/v1/engines          -> what adapters are available and what they can do
/v1/catalog/voices   -> what installable voices/models the user can add
/v1/voices/installed -> what voices are locally usable now
```

**Recommended catalog entry shape:**

```python
class CatalogVoiceFile(BaseModel):
    file_role: Literal["model", "config", "tokenizer", "vocoder", "embedding", "index", "license", "sample"]
    url: str
    sha256: str
    size_bytes: int

class CatalogVoiceEntry(BaseModel):
    voice_id: str                         # "piper-plus:vi_VM_meeting-medium"
    engine_id: str                        # "piper-plus"
    display_name: str
    language: str                         # BCP-47, e.g. "vi-VN"
    quality_tier: Literal["low", "medium", "high"]
    payload_kind: Literal["preset", "model-file", "embedding", "reference", "designed"]
    license: str                          # SPDX expression
    commercial_use: Literal["allowed", "restricted", "unknown"]
    recommended_for: list[str]            # ["vietnamese", "lightweight", "offline"]
    capabilities: list[str]               # ["streaming", "word-timing"] if known
    files: list[CatalogVoiceFile]
    source: str                           # repo/model card/source label
```

**Example — Piper-plus Vietnamese:**

```json
{
  "voiceId": "piper-plus:vi_VM_meeting-medium",
  "engineId": "piper-plus",
  "displayName": "Vietnamese — Meeting Medium",
  "language": "vi-VN",
  "qualityTier": "medium",
  "payloadKind": "model-file",
  "license": "MIT",
  "commercialUse": "allowed",
  "recommendedFor": ["vietnamese", "lightweight", "offline"],
  "capabilities": ["streaming"],
  "files": [
    {
      "fileRole": "model",
      "url": "https://huggingface.co/.../vi_VM_meeting-medium.onnx",
      "sha256": "...",
      "sizeBytes": 63897600
    },
    {
      "fileRole": "config",
      "url": "https://huggingface.co/.../vi_VM_meeting-medium.onnx.json",
      "sha256": "...",
      "sizeBytes": 4096
    }
  ],
  "source": "rhasspy/piper-voices"
}
```

**Why installable voice wins for P0:**

| Criterion | Why this wins |
|---|---|
| Flexible | Works for Piper model-file voices, Kokoro presets, RVC embeddings, and future clone/design artifacts |
| Clean | One catalog entry maps to one user-visible install action and one future installed `voice_id` |
| SoC | Catalog describes installable data; ModelManager installs files; VoiceRegistry routes installed descriptors; engines synthesize |
| Modular | New engine only contributes new catalog entries; no core route change |
| Standalone | Bundled catalog can ship offline; remote catalog remains signed per ADR-0007 |
| Scalable | 19 providers become catalog rows; no graph joins needed at P0 |
| Well-tested | Fixture catalog entries validate independently; install tests assert entry → files → installed voice descriptor |

**Why not full graph at P0:**

```text
engines[] + models[] + voices[]
```

That is more complete, but it adds joins and validation complexity before we need them. It also creates awkward cases: Kokoro has one base model with many preset voices; Piper has one model per voice; Chatterbox has one base model plus unlimited reference voices. A graph is correct long-term, but too heavy for the first protocol milestone.

**Boundary rule:** Catalog entries should not expose arbitrary local paths. The client sends only `voice_id` / `model_id` from the signed catalog. ModelManager resolves URLs internally, enforces allowlist, verifies SHA256, and atomically installs files per ADR-0007.

**Install flow:**

```text
GET /v1/catalog/voices
  -> returns CatalogVoiceEntry[]

POST /v1/models/install { "voiceId": "piper-plus:vi_VM_meeting-medium" }
  -> CatalogManager.resolve_voice(voiceId)
  -> ModelManager downloads files to temp/cache
  -> verify host allowlist + sha256 + sizeBytes
  -> atomic move into models/{engineId}/{voiceId}/
  -> write installed voice manifest
  -> VoiceRegistry.refresh()
```

**Installed voice manifest after install:**

```json
{
  "schemaVersion": "1.0",
  "voiceId": "piper-plus:vi_VM_meeting-medium",
  "engineId": "piper-plus",
  "displayName": "Vietnamese — Meeting Medium",
  "language": "vi-VN",
  "qualityTier": "medium",
  "license": "MIT",
  "payload": {
    "kind": "model-file",
    "modelPath": "models/piper-plus/piper-plus:vi_VM_meeting-medium/model.onnx",
    "configPath": "models/piper-plus/piper-plus:vi_VM_meeting-medium/config.json"
  }
}
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/schemas/v1/catalog.py` | Add `CatalogVoiceEntry`, `CatalogVoiceFile`, response schemas |
| `src/mery_tts/catalog/bundled/catalog-v1.json` | Use installable voice entries |
| `src/mery_tts/catalog/manager.py` | Add `resolve_voice(voice_id)` |
| `src/mery_tts/models/manager.py` | Install by catalog voice entry, not raw URL |
| `src/mery_tts/models/store.py` | Write installed voice manifest |
| `src/mery_tts/engines/voice_registry.py` | Refresh from installed voice manifests |
| `tests/unit/catalog/test_voice_entry_schema.py` | Validate sample entries and SPDX/commercial_use fields |
| `tests/unit/models/test_install_from_catalog_voice.py` | Verify install flow from entry → temp → checksum → store |
| `tests/unit/engines/test_voice_registry_from_manifest.py` | Registry loads installed manifests into descriptors |

**Testing requirements:**

```text
1. CatalogVoiceEntry round-trips JSON and rejects missing sha256/sizeBytes
2. Download URL not in allowlist -> catalog.host_not_allowed
3. Wrong sha256 -> model.checksum_mismatch and temp cleanup
4. Successful install writes installed voice manifest
5. VoiceRegistry.refresh() sees installed manifest and exposes matching VoiceDescriptor
6. Catalog entry with restricted license is visible but flagged, not silently hidden
7. No API accepts raw URL or local path from client
```

**Future P1/P2 escape hatch:** Add optional graph fields later without breaking P0:

```json
{
  "voiceId": "kokoro:af_bella",
  "engineId": "kokoro",
  "modelFamilyId": "kokoro-v1",
  "artifactGroupId": "kokoro-v1-onnx"
}
```

So P0 stays simple: **catalog entry = installable voice**. P1 can group voices by model family for storage dedupe and UI grouping.

---

## Q6 — Engine weight/model storage

**Verdict:** Use **artifact store + voice manifests**. This is the flexible choice. Do not store everything under `models/{engineId}/{voiceId}/...` as the final architecture. P0 can still expose installable voices, but storage should separate reusable artifacts from user-facing voices.

**Recommended data layout:**

```text
{app_data_dir}/
  artifacts/
    {engineId}/
      {artifactId}/
        artifact.json
        files...
  voices/
    {voiceId}.json
  cache/
    temp/
      {jobId}/
```

Concrete examples:

```text
artifacts/
  kokoro/
    kokoro-v1-onnx/
      artifact.json
      model.onnx
      voices.bin
  piper-plus/
    vi_VM_meeting-medium/
      artifact.json
      model.onnx
      config.json
  neutts-air/
    neutts-air-gguf-q4/
      artifact.json
      model.gguf

voices/
  kokoro__af_bella.json
  kokoro__am_adam.json
  piper-plus__vi_VM_meeting-medium.json
```

Why not literal `voiceId` as filename? Native IDs may contain `:` or `/`, so filenames should use a deterministic safe transform (`:` -> `__`) or a slug/hash. The manifest keeps the canonical `voiceId`.

**Artifact manifest:**

```python
class InstalledArtifactManifest(BaseModel):
    schema_version: Literal["1.0"]
    artifact_id: str                     # "kokoro-v1-onnx"
    engine_id: str                       # "kokoro"
    source_catalog_id: str | None = None
    source_catalog_version: str | None = None
    license: str
    commercial_use: Literal["allowed", "restricted", "unknown"]
    files: list[InstalledArtifactFile]
    installed_at: datetime
    verified_at: datetime

class InstalledArtifactFile(BaseModel):
    file_role: Literal["model", "config", "tokenizer", "vocoder", "embedding", "index", "license", "sample"]
    relative_path: str                   # relative to artifact dir
    sha256: str
    size_bytes: int
```

**Voice manifest:**

```python
class InstalledVoiceManifest(BaseModel):
    schema_version: Literal["1.0"]
    voice_id: str                        # canonical ID, e.g. "kokoro:af_bella"
    engine_id: str
    display_name: str
    language: str
    quality_tier: Literal["low", "medium", "high"]
    license: str
    commercial_use: Literal["allowed", "restricted", "unknown"]
    artifact_refs: list[str]             # ["kokoro-v1-onnx"]
    payload: VoicePayloadUnion           # from Q1
```

Example — Kokoro preset voice sharing one artifact:

```json
{
  "schemaVersion": "1.0",
  "voiceId": "kokoro:af_bella",
  "engineId": "kokoro",
  "displayName": "Bella",
  "language": "en-US",
  "qualityTier": "high",
  "license": "Apache-2.0",
  "commercialUse": "allowed",
  "artifactRefs": ["kokoro-v1-onnx"],
  "payload": {
    "kind": "preset",
    "presetName": "af_bella"
  }
}
```

Example — Piper-plus voice where artifact and voice are nearly 1:1:

```json
{
  "schemaVersion": "1.0",
  "voiceId": "piper-plus:vi_VM_meeting-medium",
  "engineId": "piper-plus",
  "displayName": "Vietnamese — Meeting Medium",
  "language": "vi-VN",
  "qualityTier": "medium",
  "license": "MIT",
  "commercialUse": "allowed",
  "artifactRefs": ["vi_VM_meeting-medium"],
  "payload": {
    "kind": "model-file",
    "modelPath": "artifacts/piper-plus/vi_VM_meeting-medium/model.onnx",
    "configPath": "artifacts/piper-plus/vi_VM_meeting-medium/config.json"
  }
}
```

**Why artifact store + voice manifests wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Supports one-voice-one-model engines (Piper), shared-base engines (Kokoro), GGUF, HF snapshots, embeddings, and indexes |
| Clean | Separates immutable verified artifacts from user-facing voice descriptors |
| SoC | ModelStore owns files/artifacts; VoiceStore owns manifests; VoiceRegistry only reads voice manifests; adapters synthesize |
| Modular | New engine defines artifact roles and voice payloads without changing API routes |
| Standalone | Everything needed is under app data; no dependency on HuggingFace cache or engine-native hidden cache |
| Scalable | Dedupes shared base models for Kokoro/Qwen3/VoxCPM2; avoids 54 copies of the same artifact |
| Well-tested | Artifact install, checksum validation, manifest write, and registry refresh are independently testable |

**Why not alternatives:**

| Option | Rejected because |
|---|---|
| `models/{engineId}/{voiceId}/...` | Simple, but duplicates shared base models and makes future dedupe a migration problem |
| Engine-managed storage | Breaks observability and SoC; every adapter invents its own storage rules |
| HuggingFace/native cache only | Not standalone, not deterministic, weak integrity, hard to clean/delete |

**Install flow:**

```text
POST /v1/models/install { voiceId }
  -> CatalogManager.resolve_voice(voiceId)
  -> ModelManager computes artifactId(s)
  -> download to cache/temp/{jobId}/
  -> verify host allowlist + sha256 + sizeBytes
  -> atomic move into artifacts/{engineId}/{artifactId}/
  -> write artifact.json
  -> write voices/{safeVoiceId}.json
  -> VoiceRegistry.refresh()
```

**Delete flow:**

```text
DELETE /v1/models/{voiceId}
  -> remove voices/{safeVoiceId}.json
  -> if no voice manifest references artifactId anymore:
       remove artifacts/{engineId}/{artifactId}/
  -> VoiceRegistry.refresh()
```

**Important boundary:** Adapters receive resolved descriptors and paths, but they do not own artifact lifecycle. They may cache loaded model objects in memory, but disk ownership remains in `models/store.py` / `voices/store.py`.

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/models/store.py` | ArtifactStore: temp download, atomic move, artifact manifest read/write/delete |
| `src/mery_tts/voices/store.py` | NEW — VoiceStore: voice manifest read/write/delete/list |
| `src/mery_tts/models/manager.py` | Install catalog voice into artifacts + voice manifest |
| `src/mery_tts/schemas/v1/models.py` | InstalledArtifactManifest + file structs |
| `src/mery_tts/schemas/v1/voices.py` | InstalledVoiceManifest + Q1 payload union |
| `src/mery_tts/engines/voice_registry.py` | Refresh from VoiceStore manifests |
| `tests/unit/models/test_artifact_store.py` | Atomic move, checksum, orphan cleanup |
| `tests/unit/voices/test_voice_store.py` | Safe filename mapping, manifest round-trip, list/delete |
| `tests/unit/models/test_delete_refcount.py` | Shared artifact deletion only when unreferenced |

**Testing requirements:**

```text
1. ArtifactStore writes only after checksum/size validation passes
2. Failed install cleans temp dir and leaves no partial artifact/voice manifest
3. Two Kokoro voices can reference one artifact; deleting one voice does not delete artifact
4. Deleting last referencing voice deletes artifact or marks it garbage-collectable
5. VoiceStore safe filename mapping round-trips canonical voice_id
6. VoiceRegistry refresh reads voice manifests and resolves artifact-backed payloads
7. No adapter writes directly into artifact or voice stores
```

**Recommendation nuance:** Keep endpoint name `POST /v1/models/install` for compatibility with ADR-0005, but allow body to use `voiceId`. Internally, installation is now `catalog voice -> artifact(s) + voice manifest`, not raw model-only installation.

---

## Q7 — `/v1/audio/speech` response delivery mode

**Clarification:** License gating is real, but it is not core to OpenAI compat. License policy belongs in catalog/install/governance. The OpenAI route should not decide license; it only routes to an already-installed `voice_id`. Therefore Q7 for this grill should be audio delivery mode.

```text
OpenAI compat route -> validates request -> resolves alias/model/voice -> synthesize -> returns audio
Catalog/install layer -> decides whether a voice/model is allowed/restricted/blocked
```

**Verdict:** Use **blocking full-response audio for MVP**, then add **chunked HTTP streaming for P1**. Do not use SSE or WebSocket for the OpenAI-compatible endpoint.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Blocking response: synthesize full audio, return `audio/wav`/`audio/mpeg` | Smallest surface, easiest OpenAI SDK compatibility, easiest tests | Worse TTFB for long text | ✅ MVP |
| B | Chunked HTTP streaming audio bytes | Better TTFB, closer to future voice agents | More lifecycle/cancellation/backpressure tests | ✅ P1 |
| C | SSE events with base64 chunks | Observable | Not OpenAI audio-response compatible; awkward for SDKs | ❌ |
| D | Reuse WS `/v1/events` only | Existing native streaming path | OpenAI SDK cannot use it | ❌ |

**MVP endpoint behavior:**

```text
POST /v1/audio/speech
  Content-Type: application/json
  Authorization: Bearer <token>

Request:
  { "model": "tts-1", "voice": "alloy", "input": "Hello", "response_format": "wav" }

Flow:
  OpenAISpeechRequest validates body
  -> OpenAI model resolver resolves model override or auto mode
  -> OpenAIVoiceAliasResolver resolves `alloy` -> native voice_id
  -> VoiceRegistry.resolve(native_voice_id)
  -> adapter.synthesize(...) collected into complete audio buffer
  -> AudioEncoder returns bytes in requested response_format

Response:
  200 OK
  Content-Type: audio/wav
  Body: raw audio bytes
```

**Recommended request schema:**

```python
class OpenAISpeechRequest(BaseModel):
    model: str | None = None
    input: str
    voice: str
    response_format: Literal["wav", "pcm"] = "wav"  # add mp3 later only if encoder exists
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
```

**Recommended route split:**

```text
api/routes/openai_speech.py
  - transport concerns only: request validation, auth already handled, response headers

openai_compat/resolver.py
  - model + voice alias resolution

engines/voice_registry.py
  - native voice_id -> (adapter, descriptor)

audio/encoder.py
  - PCMChunk[] -> wav/pcm bytes
```

**Why A MVP -> B P1 wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | MVP supports OpenAI SDK-compatible call now; P1 adds `stream=true` without changing native engine abstractions |
| Clean | Blocking response is one route, one request schema, one encoder path |
| SoC | Route does transport; resolver does OpenAI mapping; VoiceRegistry routes; adapter synthesizes; audio encoder formats bytes |
| Modular | Streaming later is a transport upgrade, not an engine rewrite, because adapters already return `AsyncIterator[PCMChunk]` |
| Standalone | Works with fake adapter and in-memory chunks; no Zam Reader, no WebSocket client, no real engine required |
| Scalable | Long-term supports many engines because output normalizes to PCM chunks before encoding |
| Well-tested | Contract tests can assert status, content-type, bytes header, invalid alias, invalid model, fake PCM output |

**P1 streaming upgrade:**

```text
POST /v1/audio/speech { ..., "stream": true }
  -> same resolver path
  -> adapter.synthesize(...) async iterator
  -> StreamingResponse yields encoded chunks
  -> cancellation on client disconnect
```

Do not implement P1 streaming until MVP blocking route is stable and tested. Native WS `/v1/events` can continue to handle low-latency streaming for Zam Reader during MVP.

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/api/routes/openai_speech.py` | NEW — blocking `/v1/audio/speech` route |
| `src/mery_tts/openai_compat/schemas.py` | `OpenAISpeechRequest` schema |
| `src/mery_tts/openai_compat/resolver.py` | Resolve model + voice alias into native `voice_id` |
| `src/mery_tts/audio/encoder.py` | PCM chunks -> WAV/PCM bytes |
| `tests/contract/api/test_openai_speech.py` | Fake adapter route tests |
| `tests/unit/audio/test_encoder.py` | WAV header, PCM byte correctness |

**Testing requirements:**

```text
1. Valid request returns 200 with `Content-Type: audio/wav`
2. Native voice_id works without alias
3. OpenAI alias works through OpenAIVoiceAliasResolver
4. Unknown voice returns `voice.not_found`
5. Unknown model returns `model.not_found` or `engine.unavailable`
6. Fake adapter chunks are collected and encoded into valid WAV bytes
7. Route does not require WebSocket, Zam Reader, real model files, or network
8. Client disconnect / cancellation is covered in P1 streaming tests, not MVP blocking tests
```

**Recommendation nuance:** This does not abandon streaming. It sequences it correctly: MVP OpenAI compat proves compatibility and routing; P1 streaming improves TTFB using the already-existing `AsyncIterator[PCMChunk]` engine contract.

---

## Q8 — OpenAI-compatible error mapping

**Verdict:** Use a **route-specific error adapter**. Native Mery routes keep the native error taxonomy; only OpenAI-compatible routes translate domain/API errors into OpenAI-style error responses.

Native Mery error taxonomy stays canonical:

```text
voice.not_found
engine.unavailable
model.not_installed
auth.invalid_token
request.too_large
synthesis.failed
```

OpenAI-compatible routes expose OpenAI-style JSON errors:

```json
{
  "error": {
    "message": "Voice not found: alloy",
    "type": "invalid_request_error",
    "param": "voice",
    "code": "voice_not_found"
  }
}
```

**Recommended module:**

```text
src/mery_tts/openai_compat/
  errors.py      # map_mery_error_to_openai(...)
  schemas.py     # OpenAIErrorResponse, OpenAIErrorObject
```

**Schema sketch:**

```python
class OpenAIErrorObject(BaseModel):
    message: str
    type: Literal[
        "invalid_request_error",
        "authentication_error",
        "permission_error",
        "not_found_error",
        "rate_limit_error",
        "server_error",
    ]
    param: str | None = None
    code: str | None = None

class OpenAIErrorResponse(BaseModel):
    error: OpenAIErrorObject
```

**Mapper sketch:**

```python
def map_mery_error_to_openai(error: LocalTTSError) -> tuple[int, OpenAIErrorResponse]:
    match error.code:
        case "voice.not_found":
            return 400, OpenAIErrorResponse(error=OpenAIErrorObject(
                message=error.message,
                type="invalid_request_error",
                param="voice",
                code="voice_not_found",
            ))
        case "engine.unavailable":
            return 503, OpenAIErrorResponse(error=OpenAIErrorObject(
                message=error.message,
                type="server_error",
                param="model",
                code="engine_unavailable",
            ))
        case "model.not_installed":
            return 404, OpenAIErrorResponse(error=OpenAIErrorObject(
                message=error.message,
                type="not_found_error",
                param="model",
                code="model_not_installed",
            ))
        case "auth.invalid_token":
            return 401, OpenAIErrorResponse(error=OpenAIErrorObject(
                message="Invalid authentication token",
                type="authentication_error",
                code="invalid_api_key",
            ))
        case "request.too_large":
            return 413, OpenAIErrorResponse(error=OpenAIErrorObject(
                message=error.message,
                type="invalid_request_error",
                param="input",
                code="request_too_large",
            ))
        case _:
            return 500, OpenAIErrorResponse(error=OpenAIErrorObject(
                message="Synthesis failed",
                type="server_error",
                code="synthesis_failed",
            ))
```

**Recommended route behavior:**

```python
@router.post("/v1/audio/speech")
async def create_speech(request: OpenAISpeechRequest) -> Response:
    try:
        native_voice_id = resolver.resolve_voice(request.voice)
        adapter, voice = voice_registry.resolve(native_voice_id)
        audio = await synthesize_full_response(adapter, voice, request.input)
        return Response(content=audio, media_type="audio/wav")
    except LocalTTSError as exc:
        status, body = map_mery_error_to_openai(exc)
        return JSONResponse(status_code=status, content=body.model_dump())
```

**Why route-specific adapter wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Native routes can evolve their own error taxonomy; OpenAI routes can mimic OpenAI SDK expectations |
| Clean | One explicit translation boundary instead of mixed native/OpenAI error shapes across code |
| SoC | Domain raises `LocalTTSError`; OpenAI compat layer translates; route serializes |
| Modular | Adding another compat API later (e.g. ElevenLabs-style) means adding another error adapter, not changing domain errors |
| Standalone | Mapper is pure function; no server, engine, network, or Zam Reader needed for tests |
| Scalable | More native error codes become table rows / match cases; no cross-layer coupling |
| Well-tested | Unit-test every mapping; route contract tests assert OpenAI JSON shape and HTTP status |

**Boundary rule:** Never make domain modules raise OpenAI-shaped errors. OpenAI compatibility is an edge adapter, not a domain concern.

```text
Domain/core error -> LocalTTSError(code="voice.not_found")
OpenAI route edge -> map to OpenAIErrorResponse
Native route edge -> map to native Mery error response
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/openai_compat/errors.py` | NEW — pure mapper from `LocalTTSError` to OpenAI error response |
| `src/mery_tts/openai_compat/schemas.py` | Add `OpenAIErrorObject`, `OpenAIErrorResponse` |
| `src/mery_tts/api/routes/openai_speech.py` | Catch `LocalTTSError`, use mapper |
| `tests/unit/openai_compat/test_error_mapping.py` | Exhaustive mapping tests |
| `tests/contract/api/test_openai_speech_errors.py` | Route-level JSON shape and status tests |

**Testing requirements:**

```text
1. `voice.not_found` -> 400 invalid_request_error, param=voice, code=voice_not_found
2. `engine.unavailable` -> 503 server_error, param=model, code=engine_unavailable
3. `model.not_installed` -> 404 not_found_error, param=model, code=model_not_installed
4. `auth.invalid_token` -> 401 authentication_error, code=invalid_api_key
5. `request.too_large` -> 413 invalid_request_error, param=input, code=request_too_large
6. Unknown LocalTTSError -> 500 server_error, code=synthesis_failed
7. Native `/v1/*` routes remain unaffected and keep native error shape
8. Mapper is pure and testable without FastAPI TestClient
```

**Recommendation nuance:** Do not overfit to exact OpenAI private behavior. Match the public response shape and broad error categories enough for SDK/tool compatibility, while preserving Mery's native taxonomy internally.

---

## Q9 — Auth model for OpenAI compat

**Verdict:** Reuse the existing Mery bearer token for MVP. Do not create a separate OpenAI-specific API key system yet. If real multi-client key management becomes necessary, add optional OpenAI-compatible API keys in P1.

**MVP behavior:**

```text
Authorization: Bearer <mery-token>
```

OpenAI SDK setup:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8765/v1",
    api_key="<mery-token>",
)

speech = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello from Mery",
)
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Reuse same Mery token | Smallest surface, secure, matches ADR-0006, OpenAI SDK already sends Bearer | User must paste Mery token as API key | ✅ MVP |
| B | Accept any non-empty bearer token | Easiest SDK setup | Insecure; violates local threat model | ❌ |
| C | Separate OpenAI-compatible API keys | Flexible for many clients | New secret store, revocation, UI, tests | ✅ P1 if needed |
| D | No auth on localhost | Convenient | Bad security; violates ADR-0006 | ❌ |

**Recommended module boundary:**

```text
security/
  token.py             # existing Mery token validation remains canonical
  api_keys.py          # P1 only, optional compat key store

api/middleware/
  auth.py              # applies to native + OpenAI routes

openai_compat/
  schemas.py
  resolver.py
  errors.py
  # no auth logic here
```

**Why A MVP -> C P1 wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | MVP works with OpenAI SDK immediately; P1 can add per-client keys without breaking existing token auth |
| Clean | One auth mechanism at MVP; no duplicate token validation logic |
| SoC | Security layer owns auth; OpenAI compat layer owns protocol translation only |
| Modular | Adding OpenAI-compatible keys later is a `security/api_keys.py` extension, not route rewrite |
| Standalone | No external identity provider, no cloud, no Zam Reader dependency |
| Scalable | Single-user local helper starts simple; future multiple clients can get scoped keys/revocation |
| Well-tested | Same auth middleware tests apply to native and OpenAI routes; P1 keys can be tested independently |

**Security boundary:** OpenAI compat must not weaken ADR-0006. The endpoint remains localhost-only and authenticated. It should reject:

```text
- missing Authorization header
- malformed Bearer token
- wrong Mery token
- unknown P1 compat key, if/when compat keys exist
```

**P1 optional compat key design:**

```python
class CompatApiKey(BaseModel):
    key_id: str
    key_hash: str              # never store raw key
    label: str                 # "Cursor", "OpenAI SDK test", etc.
    scopes: set[Literal["speech.create", "voices.read"]]
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
```

Resolution order in P1:

```text
1. If token matches primary Mery token -> allow
2. Else if token matches active compat API key with required scope -> allow
3. Else reject auth.invalid_token
```

**Files affected when implementing MVP:**

| File | Change |
|---|---|
| `src/mery_tts/api/routes/openai_speech.py` | Protected by existing auth dependency/middleware |
| `src/mery_tts/api/middleware/auth.py` | Ensure OpenAI route is not excluded |
| `tests/contract/api/test_openai_speech_auth.py` | Missing/wrong/valid bearer token cases |
| `docs/grills/openai-comp/01-voice-descriptor-and-engine-selection.md` | This decision record |

**Files affected if implementing P1 compat keys:**

| File | Change |
|---|---|
| `src/mery_tts/security/api_keys.py` | NEW — hashed compat API key store/validation |
| `src/mery_tts/settings/config.py` | Persist compat keys in app data config or dedicated key store |
| `src/mery_tts/cli/api_keys.py` | Optional CLI: create/list/revoke keys |
| `tests/unit/security/test_api_keys.py` | Hashing, scope, revoke, last-used behavior |

**Testing requirements:**

```text
1. `/v1/audio/speech` with no Authorization -> 401 OpenAI-shaped auth error
2. Wrong Bearer token -> 401 OpenAI-shaped auth error
3. Valid Mery token -> route reaches resolver/synthesis path
4. Auth middleware behavior remains identical for native routes
5. OpenAI compat layer contains no token parsing or secret validation code
6. P1 compat keys, if added, store only hashes and enforce scopes
```

**Recommendation nuance:** OpenAI SDK's `api_key` field does not need to be a real OpenAI key. It only needs to populate the `Authorization: Bearer ...` header. So reusing the Mery token is the lightest secure compat path.

---

## Q10 — Endpoint path strategy

**Verdict:** Add the OpenAI-compatible speech route directly at **`POST /v1/audio/speech`**. This is the lightest path that preserves the distribution hack: existing OpenAI-compatible clients can point `base_url` at Mery and call speech without a custom adapter.

OpenAI SDK setup:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8765/v1",
    api_key="<mery-token>",
)

speech = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello from local Mery",
)
```

This resolves to:

```text
POST http://127.0.0.1:8765/v1/audio/speech
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | `POST /v1/audio/speech` | OpenAI SDK works with standard `base_url=/v1`; maximum distribution value | Shares `/v1` namespace with native routes | ✅ MVP |
| B | `POST /openai/v1/audio/speech` | Cleaner namespace separation | Requires non-standard `base_url=/openai/v1`; weaker distribution hack | ❌ |
| C | Separate local port for OpenAI compat | Strong isolation | More config, firewall prompts, lifecycle failure modes | ❌ |
| D | Native route only + custom client adapter | Clean native API | Loses OpenAI-compatible app ecosystem | ❌ |

**Namespace guardrail:** Only the OpenAI-compatible speech route gets OpenAI-shaped semantics. Native Mery routes stay native.

```text
/v1/audio/speech       -> OpenAI-compatible edge route
/v1/engines            -> native Mery route
/v1/voices/installed   -> native Mery route
/v1/catalog/voices     -> native Mery route
/v1/models/install     -> native Mery route
/v1/events             -> native Mery WebSocket
```

Do **not** make every `/v1/*` route OpenAI-shaped just because `/v1/audio/speech` exists.

**Recommended module boundary:**

```text
api/routes/openai_speech.py
  - owns only the OpenAI-compatible endpoint path and transport response

openai_compat/
  schemas.py      # request/response/error shape
  resolver.py     # model + alias resolution
  errors.py       # native error -> OpenAI error adapter

api/routes/native_*.py
  - remain unchanged and native-shaped
```

**Why A wins under the stated design constraints:**

| Criterion | Why this wins |
|---|---|
| Flexible | OpenAI-compatible clients work now; native routes still coexist under `/v1` |
| Clean | Compatibility is isolated in one route module and `openai_compat/`, not scattered through all API code |
| SoC | Endpoint path is API transport; resolver/error/auth/engine routing stay in their modules |
| Modular | If future compat APIs exist, add new route modules without changing native routes |
| Standalone | One local FastAPI app, one port, one auth token; no proxy/gateway required |
| Scalable | Keeps deployment simple as providers grow; provider count affects registries/catalog, not endpoint paths |
| Well-tested | Contract tests hit `/v1/audio/speech` with fake adapter; native route tests remain independent |

**Testing requirements:**

```text
1. `POST /v1/audio/speech` exists and returns audio for valid fake adapter request
2. OpenAI SDK-compatible base URL `/v1` can call the route shape
3. Native routes keep native error shapes and are not affected by OpenAI error mapper
4. Missing/wrong bearer token on `/v1/audio/speech` returns OpenAI-shaped auth error
5. Unknown native route still follows normal FastAPI/native behavior
6. Route is included in OpenAPI docs with OpenAI-compatible request schema
```

**Recommendation nuance:** `POST /v1/audio/speech` is allowed to be OpenAI-compatible while the rest of `/v1` remains Mery-native because endpoint semantics are route-local. The namespace is shared, but the compatibility adapter boundary is explicit in code.

---

## Q11 — Compatibility scope: mimic OpenAI how far?

**Verdict:** Accept an OpenAI-like request schema, but explicitly reject unsupported values. Do not silently ignore fields. Do not attempt full OpenAI parity in MVP.

OpenAI-style request shape:

```json
{
  "model": "tts-1",
  "input": "Hello",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0
}
```

**MVP supported subset:**

| Field | MVP support | Behavior |
|---|---:|---|
| `model` | ✅ | Optional; maps to explicit engine/model override or OpenAI legacy alias |
| `input` | ✅ | Required text input; enforce Mery text length limit |
| `voice` | ✅ | Required; OpenAI alias or native Mery `voice_id` |
| `response_format` | ✅ partial | `wav` and `pcm` only in MVP |
| `speed` | ✅ guarded | Accept `1.0`; reject other values until adapter support exists |
| unknown fields | ❌ | Reject with structured unsupported-parameter error |
| `stream` | ❌ MVP / ✅ P1 | Reject in MVP; P1 chunked HTTP streaming |

**Recommended request schema:**

```python
class OpenAISpeechRequest(BaseModel):
    model: str | None = None
    input: str
    voice: str
    response_format: Literal["wav", "pcm"] = "wav"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def reject_unsupported_speed(self) -> Self:
        if self.speed != 1.0:
            raise UnsupportedOpenAIParameter(
                param="speed",
                code="unsupported_parameter",
                message="Mery MVP accepts speed=1.0 only.",
            )
        return self
```

**Unsupported response example:**

```json
{
  "error": {
    "message": "Mery MVP supports response_format=wav or pcm.",
    "type": "invalid_request_error",
    "param": "response_format",
    "code": "unsupported_response_format"
  }
}
```

**Why B wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Schema can grow field-by-field as codecs/streaming/speed control become real |
| Clean | Unsupported behavior is explicit and testable, not hidden in route conditionals |
| SoC | `openai_compat/schemas.py` owns request validation; route owns transport; adapters own actual feature support |
| Modular | Adding `mp3` means adding encoder + schema literal + tests, not changing the engine contract |
| Standalone | MVP works with only WAV/PCM and fake adapter; no codec/network/external service needed |
| Scalable | Provider-specific features stay behind capability checks instead of expanding route magic |
| Well-tested | Validation matrix covers every accepted/rejected field and maps to OpenAI-shaped errors |

**Why not alternatives:**

| Option | Rejected because |
|---|---|
| Full OpenAI parity | Pulls codec deps and feature complexity into MVP before route compatibility is proven |
| Minimal schema only | Too brittle for real OpenAI clients that send `speed` or `response_format` |
| Ignore unknown fields | Silent bugs; user thinks `speed=2.0` works when it is ignored |

**Capability gating rule:** Request validation checks generic OpenAI schema first; capability validation checks engine/voice-specific support second.

```text
1. OpenAISpeechRequest validates field shape and allowed MVP values
2. Resolver maps model + voice into native VoiceDescriptor
3. Capability checker verifies chosen engine/voice supports requested behavior
4. Route synthesizes or returns OpenAI-shaped unsupported error
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/openai_compat/schemas.py` | `OpenAISpeechRequest`, strict extra handling, unsupported parameter validation |
| `src/mery_tts/openai_compat/errors.py` | Unsupported format/parameter error mapping |
| `src/mery_tts/openai_compat/capabilities.py` | Optional helper: validate request vs. VoiceDescriptor/EngineDescriptor |
| `src/mery_tts/audio/encoder.py` | WAV/PCM encoders only for MVP |
| `tests/unit/openai_compat/test_speech_request_schema.py` | Validation matrix |
| `tests/contract/api/test_openai_speech_unsupported.py` | Route-level unsupported format/speed/unknown field tests |

**Testing requirements:**

```text
1. Valid minimal request defaults response_format=wav and speed=1.0
2. response_format=wav returns audio/wav
3. response_format=pcm returns raw PCM media type
4. response_format=mp3 returns OpenAI-shaped unsupported_response_format
5. speed=1.0 accepted; speed=1.25 rejected with param=speed
6. Unknown extra field rejected, not ignored
7. Error response uses OpenAI shape through Q8 mapper
8. Future encoder addition requires schema + encoder + route contract test together
```

**Recommendation nuance:** This is honest compatibility. Mery should look like OpenAI enough for clients to integrate, but it should never pretend unsupported features work. The moment a feature is supported, add it explicitly to the schema and tests.

---

## Q12 — Integration test strategy

**Verdict:** Use **unit tests + FastAPI contract tests + one OpenAI SDK smoke test with fake adapter**. Real engine tests remain optional and marked. This proves the compatibility path without downloads, real model files, GPU, Zam Reader, or network.

**Recommended layers:**

```text
unit tests
  -> openai_compat aliases/errors/schemas/resolver/capabilities
  -> audio encoder WAV/PCM bytes
  -> VoiceRegistry routing with fake descriptors

contract tests
  -> FastAPI app + fake EngineAdapter + fake VoiceRegistry
  -> POST /v1/audio/speech returns audio bytes
  -> auth, unknown voice, unsupported format, error mapping

SDK smoke test
  -> OpenAI(base_url=local_test_server/v1, api_key=test_token)
  -> client.audio.speech.create(...)
  -> validates real SDK call shape against Mery route

engine tests
  -> optional @pytest.mark.engine only
  -> not required for default CI
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Unit tests only | Fast | Does not prove FastAPI route or OpenAI shape works | ❌ |
| B | FastAPI contract tests with fake adapter | Strong MVP signal | Does not prove OpenAI SDK integration | ✅ required |
| C | Contract tests + OpenAI SDK smoke test | Best confidence without real engines | Adds SDK test dependency | ✅ recommended |
| D | Real engine integration tests | True end-to-end | Slow, downloads, flaky, hardware-dependent | ✅ optional only |

**Why C wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Tests edge adapters, resolver, fake engines, and optional real engines separately |
| Clean | Each layer owns one concern; no giant end-to-end test doing everything |
| SoC | OpenAI SDK smoke tests API compatibility; unit tests test pure modules; engine tests test adapters only |
| Modular | New compat feature adds unit + route tests without needing real engine install |
| Standalone | Default test suite runs offline with fake adapter and in-memory PCM chunks |
| Scalable | 19 providers do not multiply CI cost; each real engine can have optional marked contract tests |
| Well-tested | Proves schema, routing, auth, error shape, audio bytes, and SDK compatibility |

**Test fixture architecture:**

```text
tests/conftest.py
  fake_engine_adapter -> EngineAdapter
  fake_voice_registry -> VoiceRegistry with one or more VoiceDescriptor fixtures
  test_app -> FastAPI app with dependency overrides
  test_token -> Mery auth token fixture

FakeEngineAdapter
  engine_id = "fake"
  accepted_voice_kinds = {"preset", "model-file"}
  voices() -> [VoiceDescriptor(...)]
  synthesize(...) -> AsyncIterator[PCMChunk] yielding deterministic sine/zero PCM
```

**SDK smoke test sketch:**

```python
@pytest.mark.contract
async def test_openai_sdk_can_call_local_speech(test_server_url: str, test_token: str) -> None:
    client = OpenAI(base_url=f"{test_server_url}/v1", api_key=test_token)

    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="Hello from test",
        response_format="wav",
    )

    content = response.read()
    assert content.startswith(b"RIFF")  # WAV header
```

If the OpenAI Python SDK makes async test setup awkward, keep it as a narrow smoke test around a real local TestServer process, not the main route test path. FastAPI `TestClient` contract tests remain the primary deterministic proof.

**Contract test matrix:**

```text
happy path:
  valid token + alloy alias + tts-1 + wav -> 200 audio/wav + RIFF bytes
  valid token + native voice_id + model omitted -> 200 audio/wav
  response_format=pcm -> 200 raw PCM media type

auth:
  missing token -> 401 OpenAI-shaped authentication_error
  wrong token -> 401 OpenAI-shaped authentication_error

request validation:
  unknown response_format=mp3 -> 400 unsupported_response_format
  speed=1.25 -> 400 unsupported_parameter param=speed
  unknown extra field -> 400 invalid_request_error

resolution:
  unknown voice -> 400 voice_not_found param=voice
  unknown model -> 400/404 model_not_found or invalid_model param=model
  unavailable engine -> 503 engine_unavailable param=model
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `tests/unit/openai_compat/test_aliases.py` | Alias resolver precedence and native fallback |
| `tests/unit/openai_compat/test_error_mapping.py` | Q8 mapper cases |
| `tests/unit/openai_compat/test_speech_request_schema.py` | Q11 validation matrix |
| `tests/unit/audio/test_encoder.py` | WAV/PCM encoding |
| `tests/contract/api/test_openai_speech.py` | Route happy paths with fake adapter |
| `tests/contract/api/test_openai_speech_errors.py` | Route error shapes/statuses |
| `tests/contract/api/test_openai_sdk_smoke.py` | Real OpenAI SDK call against local test server |
| `tests/engine/test_*_adapter.py` | Optional marked real engine adapter tests |

**Testing requirements:**

```text
1. Default CI does not download models or require real engine packages
2. Fake adapter emits deterministic PCM so byte/header assertions are stable
3. SDK smoke test is narrow and can be skipped if openai package unavailable, unless included in dev deps
4. Every OpenAI-shaped error has both unit mapper test and route contract test
5. Native route tests prove OpenAI error mapper does not leak into native endpoints
6. Optional engine tests use @pytest.mark.engine and are excluded from default test run
```

**Recommendation nuance:** The SDK smoke test is worth it because the whole feature is a distribution hack. If Mery only passes internal FastAPI tests but fails the real OpenAI client construction/call path, the feature has not proven its value.

---

## Q13 — Implementation slicing

**Verdict:** Use a **vertical tracer bullet**. Do not start with a route-first hack, and do not attempt a foundation-only big-bang before proving the OpenAI-compatible path end-to-end.

**Recommended first slice:**

```text
OpenAI SDK
  -> POST /v1/audio/speech
  -> OpenAISpeechRequest validation
  -> OpenAI alias/model resolver
  -> VoiceRegistry.resolve(native_voice_id)
  -> FakeEngineAdapter.synthesize(...)
  -> AudioEncoder.to_wav(...)
  -> OpenAI-compatible audio response
```

This slice proves the entire architectural seam while using fake deterministic audio. It deliberately does **not** implement all 19 providers or real model downloads first.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Route-first: hardcoded `/v1/audio/speech` demo | Fastest demo | Encourages hacks; resolver/registry/errors added later under pressure | ❌ |
| B | Foundation-first: all schemas/registry/store before route | Clean theory | Slow feedback; may design untested abstractions | ❌ |
| C | Vertical tracer bullet through fake adapter | Proves architecture end-to-end while staying clean | Requires scope discipline | ✅ MVP slice |

**Slice 1 — Contract-first tracer bullet:**

```text
Goal: OpenAI SDK call returns WAV bytes via fake adapter.

Includes:
  - VoiceDescriptor union (minimum viable: PresetVoice + ModelFileVoice)
  - FakeEngineAdapter
  - VoiceRegistry resolving fake voice
  - OpenAI alias resolver with bundled default alias file
  - OpenAI request schema + error mapper
  - blocking /v1/audio/speech route
  - WAV encoder
  - FastAPI contract tests
  - OpenAI SDK smoke test

Excludes:
  - real Piper/Kokoro adapters
  - model downloads
  - artifact store persistence beyond fake fixtures
  - chunked HTTP streaming
  - mp3/opus/aac/flac
  - voice cloning
```

**Slice 2 — Real first engine:**

```text
Goal: Replace fake adapter path with one real low-risk engine.

Recommended: Piper-plus first for model-file voice path.

Includes:
  - PiperPlusAdapter emits ModelFileVoice descriptors
  - CatalogVoiceEntry for one bundled/downloadable voice
  - ArtifactStore + VoiceStore minimal persistence
  - VoiceRegistry.refresh() from installed voice manifests
  - engine-marked adapter tests optional
  - route contract tests still run with fake adapter by default
```

**Slice 3 — Preset/shared-artifact engine:**

```text
Goal: Prove shared artifact + many voices.

Recommended: Kokoro second.

Includes:
  - KokoroAdapter emits PresetVoice descriptors
  - one artifact referenced by multiple voice manifests
  - delete/refcount tests
  - /v1/engines installed_voice_count behavior
```

**Slice 4 — Catalog/install hardening:**

```text
Goal: Signed/verified install flow per ADR-0007.

Includes:
  - CatalogManager.resolve_voice(voiceId)
  - allowlist validation
  - sha256 + sizeBytes verification
  - temp cleanup on failure
  - atomic move
  - VoiceRegistry.refresh() after install
```

**Slice 5 — P1 streaming:**

```text
Goal: Add `stream=true` chunked HTTP path without changing EngineAdapter.

Includes:
  - StreamingResponse
  - client disconnect cancellation
  - backpressure tests
  - native WS remains separate
```

**Why vertical tracer bullet wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Proves the seams before committing to all provider-specific details |
| Clean | Every module is introduced for a real end-to-end path, not speculative layering |
| SoC | Route, resolver, registry, adapter, encoder, error mapper each own one step |
| Modular | Fake adapter can be swapped for Piper/Kokoro without rewriting route code |
| Standalone | First slice runs offline with fake PCM and no model files |
| Scalable | Later providers plug into proven adapter/descriptor/storage seams |
| Well-tested | Every slice has a contract-level success criterion before expanding scope |

**Concrete issue breakdown:**

```text
Issue 1: Add VoiceDescriptor union + fake voice fixtures
  Done when schema round-trip tests pass.

Issue 2: Add OpenAI compat schemas + error mapper
  Done when request validation/error mapping unit tests pass.

Issue 3: Add fake VoiceRegistry + FakeEngineAdapter path
  Done when registry resolves alias/native voice_id to fake adapter.

Issue 4: Add WAV encoder
  Done when deterministic PCM chunks produce valid RIFF/WAV bytes.

Issue 5: Add POST /v1/audio/speech blocking route
  Done when FastAPI contract test returns audio/wav from fake adapter.

Issue 6: Add OpenAI SDK smoke test
  Done when real OpenAI client can call local test server with base_url=/v1.

Issue 7: Add Piper-plus real path
  Done when one installed Piper voice can be synthesized behind same route.
```

**Testing requirements per slice:**

```text
Slice 1:
  - no real engine dependencies
  - no network
  - fake adapter only
  - route returns RIFF bytes
  - SDK smoke passes

Slice 2:
  - fake tests remain default
  - real Piper tests marked @pytest.mark.engine
  - if Piper missing, default CI still passes

Slice 3+:
  - storage and catalog tests use temp dirs
  - no test writes to real app data dir
  - install failure leaves no partial manifest/artifact
```

**Recommendation nuance:** This keeps architecture honest. The first deliverable is not a toy route; it is a complete but fake-backed vertical path. That is the right balance between demo speed and long-term modularity.

---

## Q14 — P0 definition of done

**Verdict:** Use **real-engine done** as the P0 completion bar, but keep it deliberately narrow: Q13 tracer bullet must pass with fake adapter **and** one real lightweight engine path must work behind the same `/v1/audio/speech` route. Do not require all providers, catalog hardening, streaming, or voice cloning for P0.

The selected definition is Option C, refined:

```text
P0 OpenAI compat is done when:
  1. OpenAI SDK smoke test passes through fake adapter
  2. FastAPI contract tests pass for auth/errors/unsupported params
  3. Native routes remain unaffected
  4. One real lightweight engine can synthesize through the same OpenAI route
  5. Real-engine tests are optional/marked, but manually verified before claiming P0 complete
```

**Recommended real engine for P0:** Piper-plus first.

Reason:

```text
Piper-plus = model-file voice path + lightweight + MIT + Vietnamese-capable + CPU baseline.
```

Kokoro remains the second real-engine slice because it proves preset/shared-artifact behavior, but it should not block the first P0 completion gate unless the team explicitly wants dual-engine P0.

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Minimal demo done: fake adapter returns WAV | Fast | Too weak; does not prove a usable local TTS path | ❌ |
| B | Contract-ready done: SDK + fake adapter + route/error/auth/docs | Clean merge signal | Still not user-useful without real synthesis | ❌ per user choice |
| C | Real-engine done: B + one real engine through same path | Proves actual usefulness while staying scoped | Requires optional engine setup/manual verification | ✅ P0 |
| D | Full roadmap done: streaming/catalog/all providers | Complete | Massive scope creep | ❌ |

**Precise P0 acceptance criteria:**

```text
Contract path:
  - POST /v1/audio/speech exists
  - OpenAI SDK can call base_url=http://127.0.0.1:<port>/v1
  - valid fake adapter request returns audio/wav RIFF bytes
  - missing/wrong auth returns OpenAI-shaped authentication_error
  - unknown voice/model returns OpenAI-shaped error
  - unsupported response_format/speed returns explicit unsupported error
  - native /v1 routes keep native error shape

Real engine path:
  - at least one Piper-plus voice manifest is resolvable as VoiceDescriptor(payload.kind="model-file")
  - VoiceRegistry resolves that voice_id to PiperPlusAdapter
  - POST /v1/audio/speech with that native voice_id returns non-empty audio/wav
  - failure to load Piper-plus degrades cleanly and does not break fake/contract tests
  - real-engine verification is documented as manual or @pytest.mark.engine

Documentation:
  - README or integration doc shows OpenAI SDK config using Mery token
  - supported MVP fields documented: model/input/voice/response_format=wav|pcm/speed=1.0
  - unsupported features documented: mp3/opus/aac/flac/stream/speed!=1.0
```

**What is explicitly not required for P0:**

```text
- all 19 providers
- Kokoro if Piper-plus is selected as the first real engine gate
- remote signed catalog refresh
- full artifact dedupe for every engine family
- chunked HTTP streaming
- mp3/opus/aac/flac encoding
- voice cloning / reference audio / designed voices
- OpenAI alias auto-selection beyond deterministic config
- fallback chains
```

**Why C can still be flexible, clean, SoC, modular, standalone, scalable, and well-tested:**

| Criterion | How C stays safe |
|---|---|
| Flexible | Fake contract path proves edge protocol; Piper proves real `model-file` voice path; Kokoro/presets can follow without route rewrite |
| Clean | Real engine integration uses the same VoiceDescriptor/VoiceRegistry/Adapter seams, not a special route shortcut |
| SoC | Route remains protocol edge; Piper adapter owns engine library calls; stores own manifests/artifacts; registry owns routing |
| Modular | Piper is one adapter behind the same ABC; future engines plug into the same contract |
| Standalone | P0 can run locally with one installed model, no Zam Reader, no cloud, no OpenAI service |
| Scalable | Real-provider count grows after the seam is proven; P0 does not multiply work by 19 |
| Well-tested | Default CI uses fake adapter; optional/marked engine tests or manual checklist prove Piper without making CI flaky |

**Recommended implementation gate:**

```text
Do not mark P0 complete from fake tests alone.
Do not require all real engines.
Do require one real engine path to pass locally before calling the feature usable.
```

**Files affected when implementing the real-engine P0 gate:**

| File | Change |
|---|---|
| `src/mery_tts/engines/piper_plus/adapter.py` | Ensure adapter emits/accepts ModelFileVoice and supports OpenAI route synthesis |
| `src/mery_tts/engines/piper_plus/model_runner.py` | Real synthesis lifecycle, warmup/cancel if applicable |
| `src/mery_tts/voices/store.py` | Store/read installed Piper voice manifest |
| `src/mery_tts/models/store.py` | Minimal artifact path for Piper ONNX/config files |
| `tests/engine/test_piper_plus_openai_speech.py` | Optional marked real-engine route test |
| `docs/integration/openai-compat.md` | User setup and supported fields |

**Testing requirements:**

```text
1. Default test suite passes without Piper-plus installed
2. @pytest.mark.engine test is skipped unless Piper-plus/model fixture is available
3. Manual P0 checklist includes one actual OpenAI SDK call returning WAV from Piper-plus
4. Piper unavailable -> EngineRegistry degrades/skips without breaking fake adapter contract tests
5. Real-engine route uses same resolver/registry/encoder path as fake adapter tests
```

**Recommendation nuance:** This is stronger than a contract-only P0 but still avoids full roadmap scope. It proves that OpenAI compatibility is not just API theater; it actually produces local speech through the same modular architecture.

---

## Q15 — First real engine gate

**Verdict:** Use **dual-engine P0: Piper-plus + Kokoro**. This aligns ADR-0004, proves two different voice payload/storage shapes, and prevents the OpenAI compat route from accidentally becoming single-engine-shaped.

The selected definition is Option C, refined:

```text
P0 real-engine gate includes:
  - Piper-plus: lightweight/model-file/Vietnamese-capable path
  - Kokoro: preset/shared-artifact/high-quality English path
```

**Why dual-engine P0 is worth the extra scope:**

| Engine | What it proves | Why it matters |
|---|---|---|
| Piper-plus | `ModelFileVoice`, artifact-per-voice-ish storage, ONNX/config files, CPU baseline, Vietnamese-capable | Proves installable voice + artifact manifest path and local baseline |
| Kokoro | `PresetVoice`, one shared artifact with many presets, quality English demo, OpenAI alias mapping | Proves aliasing (`alloy -> kokoro:af_bella`) and shared artifact architecture |

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Piper-plus first only | Smallest real-engine P0; proves model-file path | Does not prove preset/shared artifact or strong OpenAI alias demo | ❌ per user choice |
| B | Kokoro first only | Best English demo and alias mapping | Does not prove model-file/Vietnamese/local lightweight path | ❌ |
| C | Piper-plus + Kokoro in P0 | Matches ADR-0004; proves both major voice classes | Bigger P0 | ✅ selected |

**Scope guardrail:** Dual-engine P0 means exactly two real engines, not the full provider roadmap.

```text
Included:
  - Piper-plus adapter behind OpenAI route
  - Kokoro adapter behind OpenAI route
  - fake adapter remains default for contract tests
  - optional/marked real-engine tests for both
  - one Piper voice manifest
  - one Kokoro artifact with at least one preset voice manifest

Excluded:
  - remaining 17 providers
  - voice cloning/reference voices
  - designed voices
  - GPU-only engines
  - remote catalog refresh
  - streaming/mp3/full OpenAI parity
```

**Recommended P0 voice fixtures:**

```text
Piper-plus:
  voice_id: piper-plus:vi_VM_meeting-medium
  payload.kind: model-file
  role: proves Vietnamese/local lightweight path

Kokoro:
  voice_id: kokoro:af_bella
  payload.kind: preset
  role: default OpenAI alias target for alloy
```

**OpenAI alias defaults for P0:**

```json
{
  "schemaVersion": "1.0",
  "aliases": {
    "alloy": "kokoro:af_bella",
    "fable": "piper-plus:vi_VM_meeting-medium"
  }
}
```

Do not fill all six OpenAI aliases unless each target voice is actually installed/resolvable in the P0 fixture. Alias config must be honest and deterministic.

**Why C can still satisfy the design constraints:**

| Criterion | How C stays safe |
|---|---|
| Flexible | Proves both core payload families: model-file and preset; future embeddings/reference/designed voices add new payload classes, not route changes |
| Clean | Two adapters exercise the same ABC and route path; no special cases in `/v1/audio/speech` |
| SoC | Piper/Kokoro own engine library specifics; stores own artifacts/manifests; OpenAI compat only resolves and formats |
| Modular | Each engine remains an entry-point plugin; adding provider #3 is a new adapter/catalog entry, not registry rewrite |
| Standalone | Both engines run locally/CPU; no cloud/OpenAI/Zam Reader dependency |
| Scalable | Dual-engine from day one catches abstraction leaks before adding 17 more providers |
| Well-tested | Fake contract tests remain stable; real-engine tests are marked; adapter contract tests compare behavior across two engines |

**Acceptance criteria:**

```text
Contract/fake path:
  - same as Q14: OpenAI SDK smoke + fake adapter route passes

Piper-plus path:
  - adapter loads or degrades cleanly if dependency/model missing
  - emits at least one ModelFileVoice descriptor
  - OpenAI route can synthesize using native piper-plus voice_id
  - optional @pytest.mark.engine test passes when fixture is available

Kokoro path:
  - adapter loads or degrades cleanly if dependency/model missing
  - emits at least one PresetVoice descriptor
  - alias resolver maps alloy -> kokoro:af_bella
  - OpenAI route can synthesize using alias and native kokoro voice_id
  - optional @pytest.mark.engine test passes when fixture is available

Regression:
  - if either real engine is unavailable, default fake/contract tests still pass
  - unavailable engine status appears correctly in /v1/engines or is skipped per ADR-0004 import-failure policy
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/engines/piper_plus/adapter.py` | ModelFileVoice support through common adapter contract |
| `src/mery_tts/engines/piper_plus/model_runner.py` | Real Piper lifecycle/synthesis |
| `src/mery_tts/engines/kokoro/adapter.py` | PresetVoice support through common adapter contract |
| `src/mery_tts/engines/kokoro/model_runner.py` | Real Kokoro lifecycle/synthesis |
| `src/mery_tts/catalog/bundled/openai-voice-aliases-v1.json` | Honest aliases for installed/resolvable P0 voices |
| `tests/engine/test_piper_plus_openai_speech.py` | Optional real-engine OpenAI route test |
| `tests/engine/test_kokoro_openai_speech.py` | Optional real-engine OpenAI route test |
| `tests/contract/api/test_openai_speech.py` | Keep fake adapter default path |

**Testing requirements:**

```text
1. Default CI remains fake-only and does not require Piper/Kokoro packages or model downloads
2. Real-engine tests are @pytest.mark.engine and skip with clear reason when deps/fixtures missing
3. Piper and Kokoro both use the same /v1/audio/speech route/resolver/registry/encoder path
4. No route-level if engine_id == "kokoro" or if engine_id == "piper-plus" branches
5. VoiceDescriptor payload kind dispatch happens inside adapters, not API route
6. /v1/engines exposes both engines when available and degrades/skips cleanly when unavailable
```

**Recommendation nuance:** This is bigger than the minimum, but it is architecturally safer. A single real engine can hide bad abstractions. Two engines with different voice models force the plugin/registry/descriptor design to be real from P0.

---

## Q16 — Runtime dependency handling

**Verdict:** Server must start with a core-only install. Missing optional engine packages must degrade cleanly: `EngineRegistry` skips unavailable adapters, `/v1/engines` reflects what is available, and `/v1/audio/speech` returns an OpenAI-shaped `engine_unavailable` / `voice_not_found` error if no routeable engine/voice exists. Do not auto-install dependencies on first request.

This follows ADR-0004's entry-point discovery rule:

```text
Engine dependencies are optional extras.
A broken Kokoro install must not break Piper-plus.
Failed load -> logged warning, adapter skipped; registry does not crash.
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Refuse server start if no engine | Clear failure | Bad standalone/core install experience; blocks diagnostics and docs endpoints | ❌ |
| B | Server starts; missing engines skipped; speech errors clearly | Graceful, modular, testable | User must run doctor/install extras | ✅ MVP |
| C | Auto-install missing extras on first request | Convenient | Hidden network side effect, unsafe, flaky, hard to test | ❌ |
| D | Bundle Piper/Kokoro deps always | Simple UX | Core package heavier; violates optional adapter modularity | ❌ |

**Expected user flow:**

```bash
# core-only install is valid
uv tool install mery-tts-server
mery serve

# diagnostics explain missing engines
mery doctor
# -> No engine adapters available.
# -> Install engine extras:
#    uv tool install "mery-tts-server[all]"
#    or uv tool install "mery-tts-server[piper-plus]"
```

**Runtime behavior matrix:**

| Situation | `/v1/engines` | `/v1/audio/speech` |
|---|---|---|
| core only, no engines | `[]` or diagnostics status with no available engines | 503 OpenAI-shaped `engine_unavailable` |
| Piper available, Kokoro missing | Piper shown; Kokoro skipped/import warning | Piper voices work; Kokoro aliases fail clearly |
| Kokoro available, Piper missing | Kokoro shown; Piper skipped/import warning | Kokoro aliases work; Piper voices fail clearly |
| adapter package present but health fails | descriptor status `degraded/unavailable` if adapter loaded | 503 `engine_unavailable` for that engine |
| dependency import failure | adapter skipped per ADR-0004 | no routeable voice; clear error |

**Recommended implementation boundary:**

```text
engines/registry.py
  - owns entry-point discovery
  - catches import/load failures
  - records diagnostics for mery doctor and /v1/diagnostics

engines/base.py
  - EngineAdapter contract only

api/routes/openai_speech.py
  - never imports piper/kokoro directly
  - only asks VoiceRegistry to resolve voice_id

openai_compat/errors.py
  - maps engine/voice availability errors to OpenAI error shape

diagnostics/
  - turns registry load failures into actionable user messages
```

**Why B wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Users can install core, one engine, both engines, or future third-party adapters independently |
| Clean | Engine availability is a registry/diagnostics concern, not route branching |
| SoC | API route does not know package installation state; registry and diagnostics own it |
| Modular | Optional extras and entry points remain the extension mechanism |
| Standalone | Core server, health, diagnostics, catalog browsing can run without engine packages |
| Scalable | Adding 17 providers does not force all deps into the core install |
| Well-tested | Missing-engine states can be simulated with fake entry points/import failures without installing real packages |

**Error response example:**

```json
{
  "error": {
    "message": "No routeable TTS engine is available. Install an engine extra such as mery-tts-server[all].",
    "type": "server_error",
    "param": "model",
    "code": "engine_unavailable"
  }
}
```

**Diagnostics output requirement:**

```text
mery doctor
  Engine registry:
    - piper-plus: unavailable (missing optional dependency piper-plus[inference])
    - kokoro: unavailable (missing optional dependency kokoro-onnx)
  Suggested fix:
    uv tool install "mery-tts-server[all]"
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/engines/registry.py` | Graceful load/skip, diagnostics capture |
| `src/mery_tts/diagnostics/doctor.py` | Missing optional dependency checks and suggested fixes |
| `src/mery_tts/openai_compat/errors.py` | Map no-engine/no-voice states to OpenAI errors |
| `src/mery_tts/api/routes/openai_speech.py` | No direct engine imports; handle registry/voice errors only |
| `tests/unit/engines/test_registry_optional_deps.py` | Missing entry-point/import failure cases |
| `tests/unit/diagnostics/test_engine_extras.py` | Doctor suggestions for `[all]`, `[piper-plus]`, `[kokoro]` |
| `tests/contract/api/test_openai_speech_no_engines.py` | Core-only error shape |

**Testing requirements:**

```text
1. App starts when no engine adapters are loadable
2. /v1/health still works in core-only mode
3. /v1/engines returns empty or no available engines without crashing
4. /v1/audio/speech returns OpenAI-shaped engine_unavailable when no voice can resolve
5. Missing Piper does not prevent Kokoro from loading, and vice versa
6. No code path auto-installs packages or performs network I/O to resolve missing deps
7. Doctor output gives exact install command for missing extras
```

**Recommendation nuance:** This keeps Mery standalone and inspectable even when synthesis is unavailable. A local helper should be able to explain what is missing instead of refusing to boot or silently downloading packages.

---

## Q17 — Alias behavior when target voice is not installed

**Verdict:** Use deterministic alias metadata with install hints. Do not auto-install. Alias resolution should remain deterministic and data-driven, while the OpenAI error response should tell the user exactly which alias target is missing and how to fix it.

**Recommended alias config shape:**

```json
{
  "schemaVersion": "1.0",
  "aliases": {
    "alloy": {
      "voiceId": "kokoro:af_bella",
      "requiredEngine": "kokoro",
      "installHint": "uv tool install \"mery-tts-server[kokoro]\"",
      "description": "Default high-quality English voice"
    },
    "fable": {
      "voiceId": "piper-plus:vi_VM_meeting-medium",
      "requiredEngine": "piper-plus",
      "installHint": "uv tool install \"mery-tts-server[piper-plus]\"",
      "description": "Default lightweight Vietnamese-capable voice"
    }
  }
}
```

**Runtime flow:**

```text
POST /v1/audio/speech { voice: "alloy", input: "hello" }
  -> OpenAIVoiceAliasResolver.resolve("alloy")
     returns AliasResolution(alias="alloy", voice_id="kokoro:af_bella", required_engine="kokoro", install_hint="...")
  -> VoiceRegistry.resolve("kokoro:af_bella")
     fails because voice/artifact/engine is unavailable
  -> OpenAI error mapper returns voice_not_found with alias target + install hint
```

**Recommended resolver return type:**

```python
class AliasResolution(BaseModel):
    requested_voice: str                 # "alloy" or native voice_id
    resolved_voice_id: str               # "kokoro:af_bella"
    source: Literal["alias", "native"]
    required_engine: str | None = None
    install_hint: str | None = None
```

**Error response example:**

```json
{
  "error": {
    "message": "OpenAI voice alias 'alloy' maps to 'kokoro:af_bella', but that voice is not installed or the Kokoro engine is unavailable. Install Kokoro with: uv tool install \"mery-tts-server[kokoro]\"",
    "type": "invalid_request_error",
    "param": "voice",
    "code": "voice_not_found"
  }
}
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Alias resolver maps string only; registry returns plain `voice.not_found` | Clean SoC | Poor UX; user cannot tell alias target is missing | ❌ |
| B | Alias resolver checks VoiceRegistry before returning | Better error | Couples resolver to runtime registry availability | ❌ |
| C | Alias config includes target metadata + install hints; registry still resolves actual availability | Best UX while preserving boundaries | Slightly richer config | ✅ MVP |
| D | Auto-install alias target | Convenient | Hidden network/side effect; unsafe; hard to test | ❌ |

**Why C wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Alias metadata can point to Kokoro, Piper, or future engines and can carry engine-specific hints |
| Clean | Resolver is still pure data resolution; VoiceRegistry still owns runtime availability |
| SoC | Alias config owns alias intent; registry owns installed/healthy state; error mapper combines context for UX |
| Modular | Adding aliases is data-only; no route or adapter changes |
| Standalone | Hints work offline and do not trigger network/package installation |
| Scalable | Alias entries can grow with providers without adding conditional code |
| Well-tested | Unit-test resolver metadata; contract-test missing alias target error with fake registry |

**Boundary rule:** The alias resolver must not import or query `VoiceRegistry`. It should return alias metadata. The route or resolver orchestration layer can pass that metadata along when registry resolution fails.

```text
openai_compat/aliases.py
  -> pure alias name -> AliasResolution

engines/voice_registry.py
  -> resolved_voice_id -> adapter/descriptor or LocalTTSError

openai_compat/errors.py
  -> LocalTTSError + optional AliasResolution context -> OpenAIErrorResponse
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/openai_compat/aliases.py` | AliasResolution model + metadata/hint loading |
| `src/mery_tts/catalog/bundled/openai-voice-aliases-v1.json` | Rich alias entries instead of string-only mappings |
| `src/mery_tts/openai_compat/errors.py` | Include alias context in voice_not_found message |
| `src/mery_tts/api/routes/openai_speech.py` | Preserve AliasResolution context through registry resolution |
| `tests/unit/openai_compat/test_aliases.py` | Rich alias config parsing + native fallback |
| `tests/contract/api/test_openai_speech_alias_missing.py` | Alias target missing includes voice_id + install hint |

**Testing requirements:**

```text
1. Alias config parses rich entries and rejects missing voiceId
2. Native voice_id bypasses alias metadata with source=native
3. Alias target missing returns OpenAI-shaped voice_not_found with alias + target voice_id
4. Missing required engine includes installHint when configured
5. Resolver remains pure: no VoiceRegistry dependency/import
6. No request path auto-installs dependencies, downloads models, or mutates storage
7. Updating alias config is data-only and does not require route changes
```

**Recommendation nuance:** This preserves the clean architecture while avoiding a frustrating UX. Users get a deterministic answer: what alias means, what target is missing, and how to install the required engine — but Mery never performs hidden installs.

---

## Q18 — Where to document OpenAI compat for users?

**Verdict:** Create a dedicated integration guide at `docs/integration/openai-compat.md`, and add only a short link/summary in the main README. Do not put the full guide only in README, generated OpenAPI docs, or CLI help.

**Recommended docs structure:**

```text
docs/integration/openai-compat.md
  - What this is
  - OpenAI SDK setup
  - curl example
  - auth/token setup
  - supported MVP fields
  - unsupported fields and expected errors
  - voice aliases and native voice_id fallback
  - troubleshooting engine_unavailable / voice_not_found
  - mery doctor commands
  - testing/smoke command

README.md
  - short "OpenAI-compatible speech endpoint" section
  - link to docs/integration/openai-compat.md
```

**Options considered:**

| Option | Design | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Main README only | Most visible | README becomes too large and mixes quickstart with protocol details | ❌ |
| B | Dedicated `docs/integration/openai-compat.md` + README link | Clean, discoverable, extensible | One more docs file | ✅ MVP |
| C | Generated OpenAPI docs only | Auto-generated | Not enough examples/troubleshooting/user context | ❌ |
| D | CLI `mery openai --help` only | Useful at terminal | Hidden from docs/readme; not enough for SDK examples | ❌ |

**Recommended guide outline:**

```markdown
# OpenAI-compatible speech endpoint

## Quickstart

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8765/v1",
    api_key="<mery-token>",
)

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello from local Mery",
    response_format="wav",
)

response.stream_to_file("speech.wav")
```

## curl

```bash
curl -X POST http://127.0.0.1:8765/v1/audio/speech \
  -H "Authorization: Bearer $MERY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","voice":"alloy","input":"Hello","response_format":"wav"}' \
  --output speech.wav
```

## Supported MVP fields

| Field | Supported |
|---|---|
| `model` | optional; `tts-1`, `tts-1-hd`, native engine id, or `mery/<engine_id>` |
| `input` | required |
| `voice` | OpenAI alias or native Mery `voice_id` |
| `response_format` | `wav`, `pcm` |
| `speed` | `1.0` only in MVP |

## Unsupported MVP fields/formats

- `mp3`, `opus`, `aac`, `flac`
- `stream=true`
- `speed != 1.0`
- unknown request fields

## Troubleshooting

### `engine_unavailable`

Run:

```bash
mery doctor
uv tool install "mery-tts-server[all]"
```

### `voice_not_found`

Check installed voices:

```bash
curl http://127.0.0.1:8765/v1/voices/installed -H "Authorization: Bearer $MERY_TOKEN"
```
```

**Why B wins:**

| Criterion | Why this wins |
|---|---|
| Flexible | Dedicated doc can grow with P1 streaming/codecs without bloating README |
| Clean | README stays a product quickstart; integration details live in integration docs |
| SoC | Docs mirror architecture: OpenAI compat guide is one protocol/integration guide |
| Modular | Future compatibility docs (ElevenLabs, Native Messaging, SDKs) can live beside it |
| Standalone | Guide explains local token, local server, no OpenAI cloud dependency |
| Scalable | Troubleshooting and supported-field matrix can evolve as features grow |
| Well-tested | Docs can include smoke-test commands that match Q12 contract/SDK tests |

**Files affected when implementing:**

| File | Change |
|---|---|
| `docs/integration/openai-compat.md` | NEW — full user-facing integration guide |
| `README.md` | Add short link/summary only |
| `tests/contract/api/test_openai_sdk_smoke.py` | Keep smoke example aligned with docs |
| `docs/grills/openai-comp/01-voice-descriptor-and-engine-selection.md` | This decision record |

**Documentation acceptance criteria:**

```text
1. A user can configure OpenAI Python SDK from the doc without guessing base_url/api_key
2. curl example produces a WAV file when Mery is running and a voice is installed
3. Supported/unsupported fields match OpenAISpeechRequest schema
4. Troubleshooting covers engine_unavailable and voice_not_found
5. README links to the guide but does not duplicate it
6. Examples use local Mery token, not a real OpenAI API key
```

**Recommendation nuance:** Generated OpenAPI docs are still useful for schema browsing, but they cannot replace a practical integration guide with examples and failure modes. The dedicated doc should be the canonical user-facing reference.

---

## Q19 — Next feature after P0 OpenAI compat

**Verdict:** After P0 blocking OpenAI-compatible speech is stable, the next feature should be **chunked HTTP streaming for `POST /v1/audio/speech`**. This continues the Protocol-first strategy and turns the OpenAI-compatible endpoint from “generate a whole file” into a low-latency path suitable for voice-agent use.

**Recommended P1 behavior:**

```text
POST /v1/audio/speech { ..., "stream": true }
  -> same auth/model/alias/error path as blocking MVP
  -> VoiceRegistry.resolve(native_voice_id)
  -> adapter.synthesize(...) returns AsyncIterator[PCMChunk]
  -> FastAPI StreamingResponse yields audio chunks
  -> client disconnect triggers cancellation
```

**Options considered:**

| Option | Feature | Pros | Cons | Verdict |
|---|---|---|---|---|
| A | Chunked HTTP streaming for `/v1/audio/speech` | Best protocol leverage; reduces TTFB; voice-agent ready | Backpressure/cancel tests are more complex | ✅ P1 |
| B | MP3/Opus/AAC formats | More OpenAI parity | Codec deps and packaging complexity | ❌ after streaming |
| C | Catalog/install hardening | Model registry flywheel | Larger storage/catalog scope | ❌ after streaming or parallel later |
| D | CLI/doctor UX polish | Setup becomes easier | Less product-visible; can happen alongside | ⚠️ support task |
| E | More provider/voice polish | Better demos | Engine depth, not protocol reach | ❌ after protocol leverage |

**Why streaming is the right next feature:**

| Criterion | Why this wins |
|---|---|
| Flexible | Same engine contract (`AsyncIterator[PCMChunk]`) supports blocking and streaming response modes |
| Clean | Streaming is a transport delivery mode, not a new synthesis API or engine-specific branch |
| SoC | Route owns HTTP streaming; adapter owns PCM generation; cancellation token stays in adapter/model runner |
| Modular | No provider rewrite: fake, Piper, Kokoro, and future engines all stream through the same iterator contract |
| Standalone | Can be tested with fake adapter yielding delayed deterministic chunks; no real engine/network required |
| Scalable | Enables low-TTFB voice-agent workloads without adding new providers or codecs first |
| Well-tested | Contract tests can assert chunk order, first-byte timing class, disconnect cancellation, and error-before-first-chunk behavior |

**Design rule:** Do not introduce SSE or WebSocket for the OpenAI-compatible speech endpoint. Native WS `/v1/events` remains separate. OpenAI-compatible streaming should be plain HTTP streaming because OpenAI clients and generic HTTP clients can consume it more naturally.

```text
/v1/audio/speech { stream=false/default } -> blocking full audio response
/v1/audio/speech { stream=true }          -> chunked HTTP audio response
/v1/events                                -> native Mery WebSocket events
```

**Recommended request schema extension:**

```python
class OpenAISpeechRequest(BaseModel):
    model: str | None = None
    input: str
    voice: str
    response_format: Literal["wav", "pcm"] = "wav"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    stream: bool = False
```

**Streaming response nuance:** For P1, prefer `response_format="pcm"` for true chunk streaming. WAV has a header that normally needs final length; if WAV streaming is required, use a streaming-safe WAV header with unknown/large data size only if players tolerate it. Otherwise:

```text
stream=true + response_format=pcm -> supported first
stream=true + response_format=wav -> reject initially or buffer header carefully
```

**Recommended P1 support matrix:**

| Request | P1 behavior |
|---|---|
| `stream=false, response_format=wav` | Existing blocking MVP path |
| `stream=false, response_format=pcm` | Blocking raw PCM |
| `stream=true, response_format=pcm` | Supported chunked HTTP streaming |
| `stream=true, response_format=wav` | Explicit unsupported initially unless WAV streaming header is implemented |
| `stream=true, response_format=mp3` | Unsupported until encoder exists |

**Cancellation and backpressure:**

```text
client disconnect
  -> StreamingResponse generator catches cancellation/disconnect
  -> calls adapter.cancel(session_id)
  -> model_runner CancelToken stops blocking synthesis thread when possible
  -> route exits cleanly without logging false server error
```

**Files affected when implementing:**

| File | Change |
|---|---|
| `src/mery_tts/openai_compat/schemas.py` | Add `stream: bool = False` and validation matrix |
| `src/mery_tts/api/routes/openai_speech.py` | Branch blocking vs. StreamingResponse delivery only; no engine-specific branches |
| `src/mery_tts/audio/encoder.py` | Add chunk encoder for PCM, optional streaming WAV guard |
| `src/mery_tts/engines/base.py` | No change expected if `AsyncIterator[PCMChunk]` already exists |
| `tests/contract/api/test_openai_speech_streaming.py` | Chunk order, media type, cancel/disconnect behavior |
| `tests/unit/audio/test_streaming_encoder.py` | PCM chunk encoding and unsupported WAV streaming guard |

**Testing requirements:**

```text
1. stream=false path remains unchanged and still returns full WAV bytes
2. stream=true + pcm returns chunked response with deterministic fake PCM chunks
3. first yielded chunk arrives before fake adapter completes all chunks
4. client disconnect calls adapter.cancel(session_id)
5. synthesis error before first chunk maps to OpenAI-shaped JSON error if possible
6. synthesis error after chunks started terminates stream and logs structured error
7. stream=true + unsupported response_format returns explicit unsupported_response_format before synthesis starts
8. No real engine, model file, OpenAI cloud, or Zam Reader required for streaming contract tests
```

**Recommendation nuance:** This is the best next feature because it uses the architecture we already chose instead of expanding sideways. P0 proves compatibility; P1 proves low-latency delivery. Codec parity and catalog hardening can follow once the protocol path is strong.

---

## What's next (Q20+ candidates)

When ready to continue, pick the next branch:

- **Q3 — OpenAI voice alias mapping config** — how `alloy` → `kokoro:af_bella` resolution works at P1
- **Q4 — Engine descriptor schema** — `/v1/engines` response shape (engineId, license, languages, voiceCount, capabilities, status)
- **Q5 — Catalog voice model** — how catalog describes voices vs. engines (modelId namespace; `modelId: "kokoro:af_bella"` vs `"kokoro"`?)
- **Q6 — Engine weight/model storage** — bundled vs. downloaded vs. user-provided path
- **Q7 — License gating** — should Mery refuse viral-license engines, or just warn in `/v1/engines`?
- **Q8 — TTFB streaming** — Server-Sent Events vs. WebSocket vs. chunked HTTP for first-token latency
- **Q9 — Hardware auto-detection** — at startup, should Mery probe and hide GPU-only engines from `voices/installed` if no GPU?

---

## References

- `docs/adr/ADR-0004-engine-strategy.md` — entry-point plugin discovery, EngineRegistry
- `docs/adr/ADR-0005-api-protocol.md` — REST + WebSocket hybrid, /v1/engines endpoint
- `docs/adr/ADR-0007-catalog-integrity.md` — signed catalog, Ed25519
- `docs/architecture/ARCHITECTURE.md` — EngineAdapter ABC, VoiceRegistry copy-on-write
- `docs/reports/roadmap-research/providers/` — 19 engine profiles
- `docs/reports/roadmap-research/axes/02-protocol.md` — TTFB, SSML, OpenAI compat axis
