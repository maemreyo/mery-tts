# Provider 05 — OpenVoice v2

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (voice cloning base)

---

## Overview

OpenVoice v2 is MyShell's open-source voice cloning TTS with strong cross-lingual support. The architecture decouples tone color (timbre) from base speaker TTS, enabling any-language-to-any-language voice cloning. MIT-licensed, both code and (recently) weights.

## Specifications

| Attribute | Value |
|---|---|
| **License (code)** | MIT |
| **License (weights)** | MIT (v2) |
| **Languages** | 6 (EN, ZH, JA, KO, ES, FR) |
| **Vietnamese** | ❌ |
| **Voice cloning** | ✅ 1-5s reference + style control |
| **Streaming** | ✅ (~200ms first-audio) |
| **Model size** | ~? (full pipeline smaller than XTTS) |
| **Latency P50** | ~200ms first-audio, 8x real-time |
| **Hardware** | CPU, CUDA |
| **Quantization** | fp16, int8 (planned) |
| **Maintenance** | Active (36K GitHub stars) |
| **Adoption signals** | Strong community, used in RVC ecosystem |

## Strengths

- **MIT license** (both code and weights) — fully commercial-safe
- **Cross-lingual cloning** — clone voice in any of 6 langs, generate in any other
- **Style control** — explicit emotion/accent parameters
- **Fast inference** — 8x real-time, ~200ms first-audio
- **Mature** — large community, used in RVC + downstream tools

## Weaknesses

- **No Vietnamese** — 6 langs, VI not included
- **Reference quality dependent** — 1-5s is enough but quality varies
- **No word timing** — would need external alignment
- **Style params not standardized** — engine-specific

## Voice cloning capability

- **Type:** Zero-shot, 1-5s reference audio
- **Cross-lingual:** ✅ Excellent (architecture feature)
- **Style control:** ✅ Explicit emotion/accent
- **Quality:** MOS 4.0 (good)
- **Vietnamese cloning:** Not native, but cross-lingual principle could extend

## Mery integration notes

OpenVoice v2 is the **best candidate for Mery's voice cloning axis** (when Mery is ready to add cloning):
- Fully MIT-licensed
- Active maintenance
- Cross-lingual (key for any multilingual feature)
- Architecture complements piper-plus (piper for fast, OpenVoice for cloning)

**Recommendation for Mery:** When voice cloning is added (gated by governance ADR per `axes/05-governance-and-licensing.md`), OpenVoice v2 should be the first cloning engine.

## Reference

- [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) — main repo
- [OpenVoice v2 paper](https://arxiv.org/abs/2405.10300) — cross-lingual architecture
- [OpenVoice v2 HuggingFace](https://huggingface.co/myshell-ai/OpenVoiceV2) — MIT weights

## Engine × tier classification

| Sub-item | OpenVoice v2 |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 ❌ |
| Voice cloning | Tier 2 COMMON ✅ (1-5s ref, cross-lingual) |
| SSML | Tier 3 ❌ |
| Multilingual | 6 langs |
| Vietnamese | ❌ (cross-lingual extension possible) |

## Decision status

🎯 **Target engine for voice cloning axis (P3, gated by governance).** MIT + cross-lingual = best fit.
