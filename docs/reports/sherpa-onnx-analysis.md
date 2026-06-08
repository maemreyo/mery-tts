# Sherpa-ONNX — Offline Speech Toolkit Analysis

**Date:** 2026-06-08
**Scope:** Evaluate whether mery-tts should add `sherpa-onnx` as an engine adapter
**Method:** Codebase audit + librarian research + architecture review

---

## 1. What is Sherpa-ONNX

Sherpa-ONNX is an **offline speech toolkit** built by Kaldi-FSA organization.
It replaces PyTorch with **ONNX Runtime** for inference, providing:

| Feature | Description |
|---------|-------------|
| **Speech Recognition (ASR)** | Whisper, SenseVoice, Paraformer, Conformer, etc. |
| **Text-to-Speech (TTS)** | Piper, Matcha-TTS, VITS, ZipVoice, FastSpeech2, etc. |
| **Speaker Diarization** | Offline speaker separation |
| **Voice Activity Detection (VAD)** | Silero VAD, WebRTC VAD |
| **Language Bindings** | Python, C, C++, Go, Java, Swift, Wasm |
| **Platforms** | Linux, macOS, Windows, Android, iOS, WebAssembly |
| **License** | Apache-2.0 |

Core architecture:
```
sherpa-onnx (C++)
   └── ONNX Runtime (inference engine)
       └── Model files (.onnx)
           └── TTS: Piper, Matcha, VITS, FastSpeech2, ZipVoice
```

**GitHub:** https://github.com/k2-fsa/sherpa-onnx
**Language:** C++ core with Python wrapper (both pip-installable)
**Size:** ~100+ MB wheels (includes ONNX Runtime binary)

---

## 2. Sherpa-ONNX vs. mery-tts — Positioning Comparison

| Dimension | Sherpa-ONNX | mery-tts |
|-----------|-------------|----------|
| **Primary role** | C++ inference library + multi-language bindings | Python daemon with REST/WebSocket API |
| **Target user** | Mobile/embedded/desktop developers | App/browser extension/CLI script users |
| **Abstraction level** | Low-level API (load model → synthesize) | High-level service (install → serve → call API) |
| **Deployment** | `pip install sherpa-onnx` + write code | `pip install mery-tts-server` → `mery serve` → call `/v1` |
| **Model management** | Manual (developer handles .onnx files) | Automated (installer, catalog, integrity checks) |
| **Voice catalog** | None built-in (github repo hosts models) | Bundled catalog + remote catalog API |
| **API surface** | Python/C/Go/Swift function calls | HTTP REST + WebSocket + CLI |
| **Security** | None (library) | Bearer token pairing, localhost-only binding |
| **TTS-only?** | No (ASR + diarization + VAD + TTS) | Yes (TTS-only, focused) |
| **Engine strategy** | Direct model inference | Plugin adapter architecture |

**Key tension:** Sherpa-ONNX is the *engine layer* that mery-tts already abstracts over. They are adjacent layers, not direct competitors — but they compete for the same user intent: "run TTS locally without hassle."

---

## 3. Sherpa-ONNX TTS Engines

Sherpa-ONNX supports these TTS backends out of the box:

| TTS Model | Input | Output | Quality | Model Size | Vietnamese |
|-----------|-------|--------|---------|-----------|------------|
| **Piper** | Phonemes | PCM | ★★★★☆ | 20-60 MB | ✅ |
| **Matcha-TTS** | Text | PCM | ★★★★★ | 100-200 MB | ❌ |
| **VITS** | Text | PCM | ★★★★☆ | 50-100 MB | ❌ |
| **FastSpeech2** | Text | PCM | ★★★☆☆ | 30-80 MB | ❌ |
| **ZipVoice** | Text | PCM | ★★★★☆ | 50-150 MB | ❌ |

### Piper via Sherpa-ONNX

Sherpa-ONNX has a **first-party Piper implementation** that differs from `piper-plus`:

```python
# sherpa-onnx Piper API
import sherpa_onnx

tts_config = sherpa_onnx.OfflineTtsConfig(
    model="piper-vi_VM_meeting-medium.onnx",
    tokens="piper-vi_VM_meeting-medium.onnx.tokens",
    data_dir=None,
    dict_dir=None,
)

tts = sherpa_onnx.OfflineTts(tts_config)
audio = tts.generate("Xin chào", sid=0, speed=1.0)
# audio.sample_rate, audio.samples (float32 array)
```

**Differences from `piper-plus`:**

| Aspect | sherpa-onnx Piper | piper-plus |
|--------|-------------------|------------|
| **Config format** | Separate `.tokens` file | `.onnx.json` companion file |
| **Voice switching** | `sid` parameter | Different model file per voice |
| **Speed control** | `speed` param (0.5-2.0) | `--length-scale` via CLI |
| **Language** | C++ core, Python wrapper | Pure Python binary |
| **Wheel size** | ~100 MB (includes ORT) | ~5 MB (PIP-only) |

---

## 4. Current mery-tts Engine Adapters (Baseline)

### 4.1 Adapter Architecture

Every engine in mery-tts implements `EngineAdapter` ABC:

```python
class EngineAdapter(ABC):
    engine_id: ClassVar[str]                                    # "piper-plus", "kokoro"
    accepted_voice_kinds: ClassVar[frozenset[str]]              # "model-file" or "preset"

    def health(self) -> str: ...
    def voices(self) -> tuple[VoiceDescriptor, ...]: ...
    def streaming_capability(self) -> StreamingCapabilityInfo: ...
    def cancel(self, request_id: str) -> None: ...

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]: ...
```

### 4.2 Registered Engines

```toml
# pyproject.toml
[project.entry-points."mery_tts.engines"]
piper-plus = "mery_tts.engines.piper_plus.adapter:PiperPlusAdapter"
kokoro     = "mery_tts.engines.kokoro.adapter:KokoroAdapter"
```

### 4.3 Voice Kinds

| Kind | Engine | Payload | Config Inference |
|------|--------|---------|-----------------|
| `model-file` | piper-plus | `model_path` + `config_path` | `.onnx` → `.onnx.json` |
| `preset` | kokoro | `artifact_dir` | None (fixed structure) |

---

## 5. Sherpa-ONNX Integration Feasibility

### 5.1 What's Needed

| Component | Location | Status |
|-----------|----------|--------|
| `EngineAdapter` ABC | `engines/base.py` | ✅ Exists |
| Entry-point registry | `pyproject.toml` | ✅ Pattern exists |
| Voice resolver | `voice/resolver.py` | ✅ Handles `model-file` kind |
| Config inference | `voice/resolver.py` `_infer_config_path` | ✅ `.onnx` → `.onnx.json` |
| Runtime caching | Per-adapter (`PiperRuntimeCache`, `KokoroRuntimeCache`) | ✅ Pattern exists |
| Optional dependency group | `pyproject.toml` optional-deps | ✅ Pattern exists |

### 5.2 Integration Steps

```toml
# Step 1: pyproject.toml - optional dependency
[project.optional-dependencies]
sherpa-onnx = ["sherpa-onnx>=1.10"]
all        = ["mery-tts-server[piper-plus,kokoro,sherpa-onnx]"]

# Step 2: pyproject.toml - entry-point
[project.entry-points."mery_tts.engines"]
sherpa-onnx = "mery_tts.engines.sherpa_onnx.adapter:SherpaOnnxAdapter"

# Step 3: New adapter module (not yet written)
src/mery_tts/engines/sherpa_onnx/
├── __init__.py
├── adapter.py      # SherpaOnnxAdapter(EngineAdapter)
└── config.py       # SherpaOnnxConfigReader (for .onnx.json sample rate)
```

### 5.3 Adapter Pseudocode

```python
class SherpaOnnxAdapter(EngineAdapter):
    engine_id = "sherpa-onnx"
    accepted_voice_kinds = frozenset({"model-file"})

    def __init__(self):
        self._cache: dict[str, sherpa_onnx.OfflineTts] = {}

    def _load_runtime(self, model_path: str, tokens_path: str):
        config = sherpa_onnx.OfflineTtsConfig(
            model=model_path,
            tokens=tokens_path,
        )
        return sherpa_onnx.OfflineTts(config)

    def synthesize(self, text, voice, *, request_id=None):
        runtime = self._get_cached(voice.voice_id)
        # sherpa-onnx is synchronous → offload to thread pool
        audio = await asyncio.to_thread(
            runtime.generate, text, sid=0, speed=1.0
        )
        yield PCMChunk(
            pcm=audio.samples,
            sample_rate_hz=audio.sample_rate,
            channels=1,
        )
```

**Note:** Sherpa-ONNX Piper requires a separate `.tokens` file alongside the `.onnx` model.
mery-tts's config inference (`_infer_config_path`) only handles `.onnx` → `.onnx.json`.
A new inference rule or a `SherpaOnnxConfigReader` would be needed to discover the `.tokens` file.

### 5.4 Critical Gap — Tokens File Discovery

| File Type | piper-plus | sherpa-onnx Piper |
|-----------|-----------|-------------------|
| Model | `{id}.onnx` | `{id}.onnx` |
| Config | `{id}.onnx.json` | N/A |
| Tokens | N/A | `{id}.onnx.tokens` |

The `.tokens` file contains vocabulary mappings required by sherpa-onnx's C++ phonemizer.
Without it, `OfflineTtsConfig` raises at load time.

**Solution options:**

1. **Inference**: Extend `_infer_config_path` to also infer `.tokens` for sherpa-onnx voices
2. **Explicit**: Require tokens path in `ResolvedModelFilePayload` (breaks uniform voice kind)
3. **Wrapper**: Bundle a small script that extracts tokens from `.onnx.json` at install time

### 5.5 Installer Gap

```
Current flow:
  mery models install piper-plus.en-us.lessac.medium
  → downloads: en_US-lessac-medium.onnx + en_US-lessac-medium.onnx.json

Required for sherpa-onnx:
  mery models install sherpa-onnx.xxx
  → downloads: xxx.onnx + xxx.onnx.json + xxx.onnx.tokens
```

The installer would need to know about the third `.tokens` file. Currently `jobs/worker.py` infers payload templates per engine:

```python
if voice_kind == "piper-plus":
    template = {
        "kind": "model-file",
        "relative_path": f"{artifact_id}.onnx",
    }
```

A `sherpa-onnx` branch would need to add `.tokens` to the download manifest.

---

## 6. Value-Add Analysis

### 6.1 What Sherpa-ONNX Brings

| Benefit | Impact | Effort |
|---------|--------|--------|
| **More TTS models** (Matcha, VITS, FastSpeech2, ZipVoice) | High | Medium (each model type may differ) |
| **Multi-platform binary** (C/C++/Go/Swift) | Medium | None (pip wheel handles it) |
| **ASR + diarization + VAD** (future expansion) | Medium | None (separate APIs) |
| **WASM support** (browser TTS without native binary) | Medium-High | High (mery server architecture assumes localhost) |
| **Active Kaldi-FSA ecosystem** | Medium | None |

### 6.2 What Sherpa-ONNX Does NOT Solve

| Gap | Why It Matters |
|-----|---------------|
| **No voice catalog** | mery-tts still needs to maintain its own model catalog |
| **No installer** | Download + integrity check + storage still on mery-tts |
| **No REST API** | mery-tts' value prop is the API, not the inference engine |
| **No CLI daemon** | mery-tts' `mery serve` / `mery speak` / `mery doctor` all above sherpa-onnx |
| **No pairing/auth** | Security layer stays mery-tts responsibility |

### 6.3 Effort Estimate

| Task | Complexity | Time |
|------|-----------|------|
| `SherpaOnnxAdapter` skeleton + `synthesize` | Low | 1-2 days |
| `.tokens` file discovery (inference + installer) | Medium | 1-2 days |
| Config reader for sample_rate narrowing | Low | ½ day |
| Catalog manifest with `.tokens` entries | Low | ½ day |
| Test fixtures (stub .onnx + .tokens + .onnx.json) | Low | ½ day |
| Matcha/VITS model type handling | Medium | 1-2 days per model |
| **Total (Piper only)** | | **3-5 days** |
| **Total (full model family)** | | **1-2 weeks** |

### 6.4 Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| Binary wheel availability (OS/arch combos) | High | Medium | Pin minimum version, graceful fallback error |
| `.tokens` file propagation breaks catalog | High | High | Design tokens inference before adapter code |
| Model format drift (sherpa-onnx API changes) | Medium | Low | Pin exact sherpa-onnx version in optional-dep |
| Duplication with existing `kokoro-onnx` engine | Low | Medium | Clearly differentiate: sherpa-onnx = broader model zoo |

---

## 7. Recommendation

**NÊN thêm sherpa-onnx** như engine adapter, với điều kiện:

1. **Phase 1 (Piper-only):** Sherpa-ONNX Piper as alternative to `piper-plus` adapter.
   - Proves integration pattern.
   - Allows benchmarking side-by-side quality/latency.
   - ~3-5 days effort.

2. **Phase 2 (expand):** Add Matcha, VITS, FastSpeech2 support once Piper pattern is proven.
   - Incremental per-model-type, not all at once.
   - ~1-2 days per model type.

3. **Condition:** Solve `.tokens` file discovery BEFORE writing adapter code.
   - The install/catalog layer must know about `.tokens` upfront or the adapter will dead-end at runtime.

**Why this alignment with mery-tts strategy:**
- ADR-0004 explicitly defines mery-tts as "**engine-agnostic cho offline TTS**".
- Adding sherpa-onnx expands the engine catalog (Piper, Matcha, VITS, ZipVoice) without breaking existing engines.
- The effort is low-ceremony: one entry-point, one optional-dep, one adapter class.
- No changes to `engines/discovery.py`, `voice/registry.py`, or `voice/resolver.py` beyond tokens inference.

---

## 8. Open Questions (Resolve Before Implementation)

| Question | Options | Default |
|----------|---------|---------|
| **Model versioning** | Pin exact sherpa-onnx version or allow range? | Pin `>=1.10,<2.0` |
| **Tokens file source** | Bundled in model zip? Downloaded separately? | Include in model archive |
| **Multi-model per voice** | Allow sherpa-onnx Piper Matcha alongside piper-plus Piper? | Yes, distinct `engine_id` |
| **Fallback logic** | If sherpa-onnx missing, fall back to piper-plus? | No — each engine is independent |

---

## 9. Sherpa-ONNX Community & Ecosystem Metrics

| Metric | Value | Source |
|--------|-------|--------|
| GitHub stars | 5,000+ ⭐ | github.com/k2-fsa/sherpa-onnx |
| Maintainer | Kaldi-FSA (Daniel Povey's group) | Official org |
| Languages | 12+ bindings (C, C++, Python, Go, Java, Swift, JS/Wasm) | GitHub README |
| Platforms | Linux, macOS, Windows, Android, iOS, Web | GitHub README |
| Active development | Yes — weekly commits, active issues | GitHub activity |
| Used in production | Yes — multiple mobile apps, embedded devices | Community reports |
| License | Apache-2.0 | LICENSE file |

**Key advantage over mery-tts' current approach:**
Sherpa-ONNX is not an **alternative to mery-tts** — it is an **expansion opportunity**.
Mery-tts adds a Sherpa-ONNX Piper engine → user gets same voice models with potentially different runtime characteristics (C++ vs Python inference path).

---

## 10. Sources

| Source | URL | Date |
|--------|-----|------|
| Sherpa-ONNX GitHub | https://github.com/k2-fsa/sherpa-onnx | 2026-06-08 |
| Sherpa-ONNX Python API | https://github.com/k2-fsa/sherpa-onnx/tree/master/python | 2026-06-08 |
| Sherpa-ONNX TTS models | https://github.com/k2-fsa/sherpa-onnx/tree/master/tts | 2026-06-08 |
| mery-tts engine ABC | `src/mery_tts/engines/base.py` | 2026-06-08 |
| mery-tts entry-points | `pyproject.toml` | 2026-06-08 |
| mery-tts voice resolver | `src/mery_tts/voice/resolver.py` | 2026-06-08 |
| mery-tts ADR-0004 | `docs/adr/` | 2026-06-08 |
| mery-tts local TTS research | `docs/reports/local-tts-solutions-research.md` | 2026-06-05 |

---

*Report generated: 2026-06-08 14:00 GMT+7*
*Research method: Codebase audit (explore) + external research (librarian) + architecture analysis*
