# Provider 03 — XTTS-v2

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (not active)

---

## Overview

XTTS-v2 is Coqui's multilingual zero-shot voice cloning TTS. It's the most downloaded TTS model on HuggingFace (12M+ downloads). Post-Coqui restructuring, the project lives in a community fork; license is ambiguous (CPML, originally).

## Specifications

| Attribute | Value |
|---|---|
| **License** | CPML (ambiguous post-Coqui, originally Coqui Public Model License) |
| **Languages** | 17 (EN, ES, FR, DE, IT, PT, PL, TR, RU, NL, CS, AR, ZH-CN, JA, KO, HU, HI) |
| **Vietnamese** | ❌ |
| **Voice cloning** | ✅ 6s reference audio (zero-shot) |
| **Streaming** | ✅ (<200ms latency in some configs) |
| **Model size** | ~750M parameters (~1.8GB fp16, ~500MB int8) |
| **Latency P50** | ~150-280ms |
| **Hardware** | CPU (slow), CUDA (best), DirectML |
| **Quantization** | fp32, fp16, int8 (limited quality) |
| **Maintenance** | Community fork only (Coqui shut down) |
| **Adoption signals** | 12M+ downloads on HuggingFace |

## Strengths

- **Multilingual** — 17 languages (most of any zero-shot engine)
- **Quality cloning** — 6-second reference is enough for high-quality voice clone
- **HuggingFace ecosystem** — well-integrated, easy to download
- **Server support** — built-in HTTP/WebSocket server (Coqui TTS server)

## Weaknesses

- **License ambiguity** — Coqui shut down; CPML license is non-standard, may have commercial use restrictions
- **No Vietnamese** — 17 langs but VI is not among them
- **No native word timing** — needs WhisperX for post-hoc alignment
- **Large model** — ~1.8GB fp16, more than piper-plus or Kokoro
- **GPU required for real-time** — CPU is too slow for production

## Voice cloning capability

- **Type:** Zero-shot, 6-second reference audio
- **Cross-lingual:** ✅ Speak any of 17 langs in cloned voice
- **Quality:** MOS 4.0 (good but not SOTA)
- **Vietnamese cloning:** Not possible (language not in training set)

## Mery integration notes

If Mery adds XTTS-v2:
- Optional dependency: `TTS>=0.22` (the community fork)
- Python API: `TTS.api.TTS` with `speaker_wav` parameter
- Subprocess vs library: XTTS Python API is heavy, may need subprocess isolation
- Quantization: int8 (limited quality) or fp16 (recommended)
- WebSocket server: `tts-server --model_name tts_models/multilingual/multi-dataset/xtts_v2`

## License risk

**This is the deal-breaker for Mery.** Coqui shut down in 2024. The CPML (Coqui Public Model License) is not OSI-approved and has unclear commercial terms. Community forks exist but inherit the same license on the model weights.

**Recommendation:** **Do not add XTTS-v2 to Mery's engine catalog** unless the license situation is clarified. Consider XTTS-v2-compatible alternatives (F5-TTS, OpenVoice v2) instead.

## Reference

- [Coqui TTS XTTS docs](https://coqui-tts.readthedocs.io/en/latest/models/xtts.html) (historical)
- [HuggingFace coqui/XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
- [openedai-speech](https://github.com/matatonic/openedai-speech) — uses XTTS, OpenAI-compat
- [Coqui TTS server](https://coqui-tts.readthedocs.io/en/latest/server.html) — reference server

## Engine × tier classification

| Sub-item | XTTS-v2 |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ (via speed parameter) |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 ❌ (WhisperX needed) |
| Voice cloning | Tier 2 COMMON ✅ (6s ref) |
| SSML | Tier 3 ❌ |
| Multilingual | 17 langs |
| Vietnamese | ❌ |

## Decision status

⚠️ **Defer due to license ambiguity.** Consider F5-TTS, OpenVoice v2, or CosyVoice 2 as alternatives.
