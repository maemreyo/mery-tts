# Provider 19 — VoxCPM2 (OpenBMB)

**Last updated:** 2026-06-05
**Status in Mery:** Strong future candidate (30 langs + voice design + 48kHz)

---

## Overview

**VoxCPM2** is OpenBMB's tokenizer-free TTS, released April 2026, built on the **MiniCPM-4** backbone. Uses a novel **diffusion autoregressive architecture** that operates on continuous speech representations (no discrete audio tokens), preserving acoustic detail that token-based systems lose. Outputs studio-quality **48kHz** audio natively (via AudioVAE V2 asymmetric encode/decode), supports 30 languages + 9 Chinese dialects, and offers three modes: voice design (text-only), controllable cloning, and ultimate cloning (reference + transcript continuation).

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | 30 + 9 Chinese dialects (VI included!) |
| **Vietnamese** | ✅ Native (one of 30 supported langs) |
| **Voice cloning** | ✅ Isolated reference + continuation modes |
| **Voice design** | ✅ Zero-shot from natural language ("deep dramatic movie trailer voice") |
| **Streaming** | ✅ RTF 0.30 (RTX 4090) or 0.13 (Nano-vLLM) |
| **Model size** | 2B parameters |
| **Latency P50** | ~150ms first chunk; sub-200ms TTFA |
| **Hardware** | GPU required (8GB VRAM) |
| **Sample rate** | 48kHz native (no upsampler) |
| **Quantization** | bf16 standard |
| **Maintenance** | Active (OpenBMB team, April 2026) |
| **Fine-tuning** | ✅ Full SFT + LoRA supported |
| **OpenAI compat** | ✅ via Nano-vLLM / vLLM-Omni |

## Strengths

- **Apache 2.0** with explicit commercial use
- **Vietnamese native** — covers Mery's Vietnamese strategy directly
- **30 languages + 9 Chinese dialects** — broad coverage
- **48kHz native output** — studio quality without post-processing
- **3 modes in one model** — voice design, controllable cloning, ultimate cloning
- **Token-free architecture** — preserves detail lost in discrete token systems
- **OpenAI-compatible serving** — drop-in for Mery's `/v1/audio/speech` path
- **LoRA fine-tuning** — easy custom voice adaptation
- **MiniCPM-4 backbone** — leverages OpenBMB's existing LLM ecosystem
- **2M+ hours training data** — competitive with OmniVoice (581k) and Qwen3-TTS (5M)

## Weaknesses

- **GPU required** (8GB VRAM minimum) — not consumer-laptop viable
- **2B params** — heavier than Supertonic (99M) or NeuTTS Air (748M)
- **Benchmarks are self-reported** — independent validation sparse (April 2026 release)
- **Voice cloning on 30 langs = average quality** per language vs. narrow specialists
- **OpenBMB is a smaller org** than Alibaba/Google — long-term sustainability question
- **Controllable cloning consistency** — developer docs admit results vary; recommend 1–3 generations

## Mery integration notes

VoxCPM2 is the **strongest 2026 OSS engine for "Vietnamese + 29 other languages" + studio-quality + voice design** in a single model. For Mery:

1. **Vietnamese strategy winner** — beats MeloTTS-Vietnamese on language coverage (30 vs. 1), comparable quality
2. **Multilingual engine** — covers the 10 most-requested langs + 20 more, including VI natively
3. **Studio-quality output** — 48kHz vs. Kokoro's 24kHz
4. **Voice design from text** — no need for reference audio for new voices
5. **OpenAI-compatible serving** — fastest path to Mery's `/v1` integration

Cost: 8GB VRAM requirement. For consumer laptops, VoxCPM2 is **not** a drop-in — but it's a strong **server-side rendering engine** for Mery's premium tier.

## Vietnamese-specific notes

VoxCPM2 lists Vietnamese as one of its 30 supported languages:
- ISO 639-3: `vie`
- Auto-detection in most cases (no explicit language tag required)
- Quality on par with other top-tier languages per OpenBMB benchmarks

For Mery's Vietnamese strategy, VoxCPM2 competes with:
- **MeloTTS-Vietnamese** — MIT, CPU-friendly, VI-specific quality
- **Supertonic 3** — MIT, on-device, 31 langs (VI included)
- **Fish Audio S2** — Research License, GPU, multilingual

## Reference

- [OpenBMB/VoxCPM GitHub](https://github.com/OpenBMB/VoxCPM) — main repo
- [openbmb/VoxCPM2 HuggingFace](https://huggingface.co/openbmb/VoxCPM2) — model weights
- [VoxCPM2 demo](https://huggingface.co/spaces/openbmb/VoxCPM-Demo) — interactive demo
- [voxcpm.com](https://voxcpm.com/en/) — official site
- [voxcpm.space](https://voxcpm.space/) — community docs

## Engine × tier classification

| Sub-item | VoxCPM2 |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ (preset + design) |
| Output format | Tier 1 BASE ✅ (48kHz native) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (RTF 0.13–0.30) |
| Word timing | Tier 3 |
| Voice cloning | Tier 3 ✅ (2 modes) |
| Voice design | Tier 3 ✅ (text-prompted) |
| SSML | Tier 3 (style instructions) |
| Multilingual | 30 langs + 9 ZH dialects |
| Vietnamese | ✅ Native |
| Studio quality | ✅ (48kHz) |
| OpenAI compat | ✅ (Nano-vLLM path) |
| GPU required | ⚠️ 8GB VRAM |
| Fine-tuning | ✅ SFT + LoRA |

## Decision status

🟢 **Strong future candidate** for Mery's Vietnamese + multilingual strategy. Best fit if Mery is willing to require GPU (8GB+) and wants studio-quality 48kHz output with voice design.

## Strategic fit

VoxCPM2 is the **single best engine to cover "Vietnamese + 29 other languages"** in 2026. Combined with:
- **Kokoro / Supertonic** (CPU/edge, 1–31 langs)
- **NeuTTS Air** (on-device English + voice cloning)
- **Chatterbox** (English quality + emotion)

…Mery covers every niche from edge to GPU, English to 30+ languages, with the right tool for each use case.

For Mery's Vietnamese strategy specifically: **VoxCPM2 vs. Supertonic** is the key decision (both have VI, both Apache 2.0/MIT, both 2026). VoxCPM2 wins on quality + voice design; Supertonic wins on footprint + speed.
