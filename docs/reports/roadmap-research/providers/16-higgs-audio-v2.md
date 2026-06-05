# Provider 16 — Higgs Audio V2 (Boson AI)

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (SOTA, 5.77B)

---

## Overview

**Higgs Audio V2** is Boson AI's open-source large TTS model, released July 2025. At 5.77B parameters, it's the **largest SOTA open-source TTS** as of mid-2026, targeting quality parity with commercial APIs (ElevenLabs, OpenAI TTS). Trained on a multi-task objective that includes TTS, voice cloning, and audio understanding, it produces natural, expressive speech with strong prosody. Apache 2.0 licensed.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | English primary; multilingual in research preview |
| **Vietnamese** | ❌ (not in initial release) |
| **Voice cloning** | ✅ (built into the multi-task training) |
| **Streaming** | ✅ |
| **Model size** | 5.77B parameters |
| **Latency P50** | Medium-slow (large model = higher compute) |
| **Hardware** | GPU required (24GB+ VRAM for fp16) |
| **Sample rate** | 24kHz / 48kHz |
| **Quantization** | fp16, fp8, int8 (with quality tradeoffs) |
| **Maintenance** | Active (Boson AI, July 2025 release) |
| **Architecture** | Multi-task audio LM (TTS + ASR + audio understanding) |

## Strengths

- **5.77B parameters** — largest open-source SOTA TTS as of 2026
- **Apache 2.0** — commercial use, no royalties
- **Multi-task training** — TTS quality benefits from joint ASR + audio understanding
- **SOTA on TTS Arena benchmarks** — competitive with ElevenLabs Pro, OpenAI TTS-1 HD
- **Voice cloning built-in** (no separate adapter)
- **Strong prosody** — natural rhythm, emphasis, pauses
- **Boson AI** — well-funded startup, active maintenance

## Weaknesses

- **5.77B params** — requires 24GB+ VRAM, not consumer-laptop viable
- **No Vietnamese** in initial release
- **Higher latency** than smaller models (Supertonic, Kokoro)
- **Energy/compute cost** — running at scale is expensive
- **New release (July 2025)** — independent benchmarks still maturing
- **Tied to GPU infrastructure** — not a "runs on anything" engine

## Mery integration notes

Higgs Audio V2 is the **"quality ceiling"** engine for Mery — when naturalness matters more than footprint. Use cases:

1. **High-fidelity content** — audiobooks, marketing content, professional narration
2. **Quality benchmark** — compare Mery's other engines against Higgs V2 as a reference
3. **Server-side rendering** — Mery can offload to a remote Higgs V2 instance when local engines aren't good enough

Not a fit for:
- **Consumer-laptop offline use** (too heavy)
- **Real-time conversational agents** (latency too high)
- **Vietnamese content** (not supported yet)

## Reference

- [boson-ai/higgs-audio-v2](https://huggingface.co/bosonai/higgs-audio-v2) — HF model
- [bosonai/higgs-audio](https://github.com/boson-ai/higgs-audio) — GitHub
- [Modal blog — top open-source TTS](https://modal.com/blog/open-source-tts) — listed #1 in 2025 rankings
- [MarkTechPost 2026 benchmark](https://www.marktechpost.com/2026/05/30/best-text-to-speech-tts-models-in-2026-a-benchmark-based-comparison) — competitive with Gemini 3.1 Flash TTS

## Engine × tier classification

| Sub-item | Higgs Audio V2 |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ (24/48kHz) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 |
| Voice cloning | Tier 3 ✅ (built-in) |
| SSML | Tier 3 |
| Multilingual | EN + research preview |
| Vietnamese | ❌ |
| Quality ceiling | ✅ SOTA |
| GPU required | ✅ (24GB+) |
| Energy cost | High |

## Decision status

🟡 **Quality-ceiling future candidate** for Mery. Not a near-term pick (too heavy for Mery's current positioning), but a strong reference point for "what's possible with OSS."

## Strategic fit

Higgs Audio V2 represents the **upper bound of open-source TTS quality** as of mid-2026. For Mery, it's useful as:
- **Reference benchmark** when evaluating other engines
- **Server-side fallback** for high-stakes content (audiobook, professional)
- **Future option** if Mery adds "premium rendering" tier

But for everyday Mery use, Kokoro/piper/Supertonic remain the right picks.
