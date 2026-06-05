# Provider 17 — Qwen3-TTS (Alibaba)

**Last updated:** 2026-06-05
**Status in Mery:** Strong future candidate (multilingual + 97ms latency)

---

## Overview

**Qwen3-TTS** is Alibaba Cloud's open-source multilingual TTS suite, released January 2026. Built on a discrete multi-codebook LM architecture with the **Qwen3-TTS-Tokenizer-12Hz**, it combines high-quality synthesis, 3-second voice cloning, voice design, and **97ms first-token latency** in a single Apache 2.0 stack. Covers 10 languages including Chinese dialects (Sichuan, Beijing, etc.). Two model sizes: 0.6B (4GB VRAM) and 1.7B (8GB VRAM).

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | 10 (ZH, EN, JA, KO, DE, FR, RU, PT, ES, IT) + Chinese dialects |
| **Vietnamese** | ❌ (not in initial 10-language set) |
| **Voice cloning** | ✅ Zero-shot from 3s reference audio |
| **Voice design** | ✅ Natural language prompts ("warm storyteller voice with gentle pacing") |
| **Streaming** | ✅ 97ms first-token latency (dual-track streaming) |
| **Model size** | 0.6B (4GB VRAM) or 1.7B (8GB VRAM) |
| **Latency P50** | 97ms first token; sub-200ms full TTFA |
| **Hardware** | NVIDIA GPU recommended; CPU not viable |
| **Sample rate** | 24kHz |
| **Quantization** | bf16/fp16 |
| **Maintenance** | Active (Alibaba Qwen team, Jan 2026) |
| **Training data** | 5M+ hours of speech |

## Strengths

- **Apache 2.0** with full commercial use grant
- **97ms first-token latency** — fastest streaming among voice-cloning-capable OSS TTS
- **10 languages** with Chinese dialect support
- **3-second voice cloning** — fastest minimum reference length in this class
- **Voice design from natural language** — describe the voice you want
- **Lowest WER in 6 of 10 languages** vs. MiniMax-Speech, ElevenLabs Multilingual v2
- **Highest speaker similarity in all 10 languages** (vs. competitors)
- **Cross-lingual cloning** — clone English, speak Japanese
- **SOTA on Seed-TTS English cloning** (1.24 WER)
- **DPO + GSPO + speaker fine-tuning pipeline** — quality alignment
- **Docker image with OpenAI-compatible API** — drop-in replacement

## Weaknesses

- **No Vietnamese** — major gap for Mery's VI strategy
- **GPU required** (4GB minimum for 0.6B, 8GB for 1.7B)
- **Multilingual not exhaustive** — 10 langs vs. OmniVoice's 600+ (different niche)
- **Newer (Jan 2026)** — independent validation still emerging
- **Not on-device** — needs server-grade hardware

## Mery integration notes

Qwen3-TTS is the **best 2026 OSS engine for multilingual + voice cloning** if Vietnamese isn't required. For Mery:

1. **Multilingual expansion engine** — 10 langs + Chinese dialects
2. **Streaming champion** — 97ms first-token beats VoxCPM2 (130ms), Fish S2 (100ms), OmniVoice (no streaming)
3. **Voice cloning + design in one** — most versatile
4. **OpenAI-compatible server** — fast path to integrate as `/v1/audio/speech` drop-in

Critical gap: **no Vietnamese**. For Mery's Vietnamese strategy, MeloTTS-VI or Supertonic remain the picks. Qwen3-TTS fits Mery's "scale to 10 languages" axis, not the "Vietnamese" axis.

## Performance benchmarks

| Metric | Qwen3-TTS 1.7B | Competitor best |
|---|---|---|
| EN WER (Seed-TTS) | 1.24% (SOTA) | MiniMax: ~1.5%, ElevenLabs Multilingual v2: ~2% |
| Speaker similarity (avg 10 langs) | Highest | 0.775 Qwen vs. lower for others |
| zh-to-ko mixed error | 4.82% | CosyVoice 3: 14.4% (66% relative reduction) |
| First-token latency | 97ms | VoxCPM2: 130ms, Fish S2: 100ms |

## Reference

- [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) — main repo
- [Qwen/qwen3-tts HuggingFace collection](https://huggingface.co/collections/Qwen/qwen3-tts) — model variants
- [Qwen/Qwen3-TTS Playground](https://huggingface.co/spaces/Qwen/Qwen3-TTS) — interactive demo
- [arxiv 2601.15621](https://arxiv.org/pdf/2601.15621v1) — paper
- [MarkTechPost 2026 release coverage](https://www.marktechpost.com/2026/01/22/qwen-researchers-release-qwen3-tts-an-open-multilingual-tts-suite-with-real-time-latency-and-fine-grained-voice-control)

## Engine × tier classification

| Sub-item | Qwen3-TTS |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ (9 preset speakers) |
| Output format | Tier 1 BASE ✅ (24kHz) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (97ms TTFA, sub-200ms full) |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | Tier 3 ✅ (3s zero-shot) |
| Voice design | Tier 3 ✅ (natural language prompts) |
| SSML | Tier 3 (emotion + style instructions) |
| Multilingual | 10 langs + ZH dialects |
| Vietnamese | ❌ |
| OpenAI compat | ✅ (Docker image) |
| GPU required | ⚠️ 4GB (0.6B) / 8GB (1.7B) |

## Decision status

🟢 **Strong future candidate** for Mery's multilingual expansion. Beats VoxCPM2 on latency, OmniVoice on streaming, Higgs V2 on footprint, Fish S2 on speed. Best fit if Mery wants "10 languages with cloning" in a single engine.

## Strategic fit

Qwen3-TTS is the **#1 pick for Mery's "scale to 10 languages" axis** (P1 priority) — if Vietnamese is solved separately by MeloTTS-VI or Supertonic, Qwen3-TTS handles the other 9 most-requested languages (ZH/EN/JA/KO/DE/FR/RU/PT/ES/IT) with the lowest latency and best cloning in class. Combined with Supertonic (for VI + 30 other langs), this gives Mery "universal coverage" without gaps.
