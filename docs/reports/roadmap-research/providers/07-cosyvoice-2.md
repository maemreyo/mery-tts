# Provider 07 — CosyVoice 2

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate

---

## Overview

CosyVoice 2 is Alibaba's FunAudioLLM project — an LLM-based TTS with 0.5B parameters, Apache 2.0 licensed, and strong zero-shot voice cloning from 3-second reference audio. Targets Chinese + 8 other languages with unified streaming/non-streaming architecture.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | 9 + 18 Chinese dialects |
| **Vietnamese** | ❌ |
| **Voice cloning** | ✅ 3s zero-shot |
| **Streaming** | ✅ 150ms TTFA, unified with non-streaming |
| **Model size** | 0.5B (~1.5GB fp16) |
| **Latency P50** | ~150ms TTFA |
| **Hardware** | CPU, CUDA |
| **Quantization** | fp16, int8 |
| **Maintenance** | Active (research project) |
| **Adoption signals** | FunAudioLLM, used in some commercial Chinese products |

## Strengths

- **Apache 2.0** — fully commercial-safe
- **Low-latency** — 150ms TTFA
- **Quality cloning** — MOS 5.53 (SOTA in some benchmarks)
- **Unified architecture** — same model for streaming and non-streaming
- **Multi-dialect Chinese** — 18 CN dialects
- **3-second reference** — shortest zero-shot requirement

## Weaknesses

- **No Vietnamese** — 9 langs + 18 CN dialects, VI not included
- **CN-centric** — Chinese is the primary use case
- **Research project** — not as packaged as piper-plus or Kokoro
- **Less active community** than OpenVoice v2 / F5-TTS

## Voice cloning capability

- **Type:** Zero-shot, 3s reference (shortest of all engines reviewed)
- **Cross-lingual:** ✅ Good
- **Quality:** MOS 5.53 (SOTA on some benchmarks)
- **Vietnamese cloning:** Not native

## Mery integration notes

CosyVoice 2 is a **strong alternative to OpenVoice v2** for voice cloning axis:
- Apache 2.0 vs MIT (both commercial-safe)
- 3s ref vs 1-5s (similar)
- Unified streaming vs separate paths (CosyVoice advantage)

**Decision matrix:**
- CosyVoice 2 if: lowest latency priority, CN languages needed
- OpenVoice v2 if: cross-lingual priority, MIT preference, more active community

## Reference

- [FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) — main repo
- [CosyVoice paper](https://arxiv.org/abs/2407.05407) — architecture
- [CosyVoice HuggingFace](https://huggingface.co/FunAudioLLM/CosyVoice-300M) — models

## Engine × tier classification

| Sub-item | CosyVoice 2 |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (150ms TTFA) |
| Word timing | Tier 3 (partial) |
| Voice cloning | Tier 2 COMMON ✅ (3s ref) |
| SSML | Tier 3 ❌ |
| Multilingual | 9 langs + 18 CN dialects |
| Vietnamese | ❌ |

## Decision status

🎯 **P3 future candidate for voice cloning axis.** Apache 2.0 makes it easier than F5-TTS. Compare to OpenVoice v2.
