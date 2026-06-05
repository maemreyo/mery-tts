# Axis 01 — Engine Layer

**Last updated:** 2026-06-05
**Status in roadmap:** Explicit
**Sub-items:** CoreML adapter, Word timing, Voice cloning

---

## What this axis covers

The engine layer is where Mery's pluggable TTS engines live. ADR-0004 already decided the dual-engine strategy (piper-plus + Kokoro) with entry-point plugin discovery. This axis covers the **next-level** engine capabilities that the base 2 engines don't fully provide.

## Sub-items

### 1.1 CoreML adapter (Apple Silicon acceleration)

**What it is:** A code path in the Kokoro engine that uses CoreML Execution Provider (EP) in ONNX Runtime to leverage the Apple Neural Engine (ANE). Currently Kokoro uses `kokoro-onnx` (CPU).

**Why it matters:**
- 25x real-time on M4, 17x on iPhone 16 Pro (per `laishere/kokoro-coreml`)
- P50 latency 27ms (piper-plus CPU) → ~10ms (ANE)
- 4-6x battery life improvement vs CPU inference
- M-series Mac users (large demographic) get materially better UX

**Cost:**
- Medium-high. Need to refactor Kokoro's ONNX graph to be ANE-friendly (no RangeDim, fixed shapes)
- Separate fp16 ANE stages from fp32 DSP stages
- Quantization: int8 palettized (75% size reduction), fp16 for ANE
- Need 2 code paths: one for Apple Silicon, one for Intel Mac (or just CPU fallback)

**Tier:** Tier 2 COMMON — most local engines target ANE/CoreML if they ship ONNX.

**Reference projects:**
- [laishere/kokoro-coreml](https://github.com/laishere/kokoro-coreml) — Kokoro with CoreML/ANE
- [onnxruntime CoreML EP docs](https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html)
- [Kokoro-FastAPI ROCm image](https://github.com/remsky/Kokoro-FastAPI/) — analogous for AMD

**Hidden risk:** Engine × ANE × CoreML × CPU = N×M test matrix. Apple Silicon only. Apple can change ANE API between macOS versions. **See `axes/04-hardware-backend-matrix.md`.**

---

### 1.2 Word timing (per-word/phoneme timestamps)

**What it is:** Exposing per-word (or per-phoneme) timing information in the WebSocket audio stream so the client can synchronize UI events (karaoke-style highlighting, dictionary lookups, language learning).

**Why it matters:**
- Zam Reader's primary UX: reading text aloud with synchronized word highlighting
- "Karaoke reading" is a known accessibility / language-learning pattern
- Without timing, the client can only highlight by elapsed-time approximation
- Tier 2 COMMON — every 2025+ serious TTS exposes it

**Cost:**
- High. Each engine has different timing extraction:
  - **piper-plus**: built-in JSON/TSV/SRT output (`--phoneme-timing` flag)
  - **Kokoro-FastAPI**: per-word timestamps via SGLang-style processing
  - **Fish Audio S2**: word-level via SGLang
  - **XTTS**: no native (Whisper reference audio needed for estimation)
- Need new WS event type: `word.boundary` with `{char_start, char_end, time_ms}`
- Need drift handling: if timing is off by 50ms, UX feels broken
- Need alignment verification (MFA or WhisperX) to validate engine-native timing

**Tier:** Tier 2 COMMON.

**Reference projects:**
- [rhasspy/piper](https://github.com/OHF-Voice/piper1-gpl) — phoneme timing output
- [Montreal Forced Aligner](https://mfa-models.readthedocs.io/en/latest/) — independent alignment verification
- [WhisperX](https://github.com/m-bain/whisperX) — ASR + alignment, multi-language

**Hidden risk:** Client uses timing to highlight — if timing drifts or is wrong, UX feels broken. Need a contract test that asserts timing accuracy on a known reference text.

---

### 1.3 Voice cloning

**What it is:** User uploads 3-30s of reference audio → Mery extracts speaker embedding → any text can be spoken in that voice.

**Why it matters:**
- The killer feature that would put Mery in ElevenLabs-tier territory
- Personal reading: clone your own voice for "read my own article back to me"
- Zam Reader use case: clone teacher voice for student practice
- Tier 3 PROVIDER-SPECIFIC today, but rapidly becoming Tier 2 in 2026

**Cost:**
- Very high (engineering) + **governance complexity** (see `axes/05-governance-and-licensing.md`)
- Zero-shot cloning: XTTS (6s ref), F5-TTS (5-15s ref), OpenVoice v2 (1-5s ref), Fish Audio S2 (10-30s ref)
- Fine-tuning: GPT-SoVITS (1-10min data, 30min training), RVC (10min data, 30min-2hr)
- Need voice encoder architecture: ECAPA-TDNN, WavLM, CLAP, HuBERT

**Tier:** Tier 3 PROVIDER-SPECIFIC.

**Reference projects:**
- [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) — MIT, cross-lingual cloning
- [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) — MIT (code), CC-BY-NC (weights)
- [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) — Research license, 80+ langs
- [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) — Apache 2.0
- [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) — MIT, fine-tuning
- [ZDisket/vits-evo](https://github.com/ZDisket/vits-evo) — ONNX voice cloning, zero-shot

**Hidden risks (multiple):**
1. **Deepfake**: cloning someone's voice without consent = crime in Texas/Tennessee, EU AI Act violation
2. **Consent records**: every cloned voice must link to documented consent
3. **Detection**: AudioSeal watermarking helps but isn't perfect
4. **Brand risk**: one viral deepfake incident = reputation destruction
5. **No undo**: once a voice is distributed, it's out there

**Recommendation:** **DEFER** voice cloning until governance ADR is written and brand has moat. Provide architecture (voice encoder interface in EngineAdapter ABC) so cloning can be added without breaking changes.

---

## Tier mapping (per sub-item)

| Sub-item | Tier | Mery's priority | ADR needed? |
|---|---|---|---|
| CoreML adapter | Tier 2 COMMON | P2 | Yes (hardware backend selection) |
| Word timing | Tier 2 COMMON | **P1** (Zam Reader is first consumer) | Yes (WS event schema) |
| Voice cloning | Tier 3 PROVIDER-SPECIFIC | **P3** (defer) | **Yes (governance first)** |

## Engine × sub-item coverage matrix

| Engine | CoreML | Word timing | Voice cloning |
|---|---|---|---|
| piper-plus | ❌ CPU only | ✅ Built-in (JSON/TSV/SRT) | ✅ Speaker embedding |
| Kokoro | ✅ via kokoro-coreml | ✅ via Kokoro-FastAPI | Limited |
| XTTS-v2 | ❌ CPU/GPU | ❌ (WhisperX needed) | ✅ 6s ref, 17 langs |
| F5-TTS | ❌ CPU/GPU | Partial | ✅ 5-15s ref, cross-lingual |
| OpenVoice v2 | ❌ | N/A | ✅ 1-5s ref, cross-lingual |
| Fish Audio S2 | ❌ CPU/GPU/SGLang | ✅ SGLang | ✅ 10-30s ref, 80+ langs |
| CosyVoice 2 | ❌ | Partial | ✅ 3s zero-shot |
| RVC | ❌ | N/A | ✅ Fine-tune, voice conversion |

## Cross-references

- `providers/` — individual engine analysis
- `axes/04-hardware-backend-matrix.md` — engine × hardware × EP selection
- `axes/05-governance-and-licensing.md` — voice cloning consent + EU AI Act
- `99-priority-matrix.md` — when to build each
