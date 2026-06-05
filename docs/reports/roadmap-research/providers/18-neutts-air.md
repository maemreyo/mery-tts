# Provider 18 — NeuTTS Air (Neuphonic)

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (on-device + voice cloning + watermarking)

---

## Overview

**NeuTTS Air** is Neuphonic's on-device TTS with instant voice cloning, released October 2025. The first "super-realistic" sub-1B TTS that runs locally on phones, laptops, and Raspberry Pi via GGUF quantization. Built on Qwen 0.5B backbone with proprietary **NeuCodec** (50Hz neural codec, 0.8 kbps, 24kHz output). Includes built-in **Perth watermarking** for content traceability — the only OSS TTS with this compliance feature.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | English only |
| **Vietnamese** | ❌ |
| **Voice cloning** | ✅ Zero-shot from 3–15s reference audio |
| **Streaming** | ✅ (real-time on mid-range devices) |
| **Model size** | 748M params (Qwen 0.5B + NeuCodec) |
| **Latency P50** | Real-time on mid-range devices (no GPU required) |
| **Hardware** | CPU-only (GGUF Q4/Q8), runs on Raspberry Pi |
| **Sample rate** | 24kHz |
| **Quantization** | GGUF Q4 (~0.5GB) or Q8 (~1GB) |
| **Maintenance** | Active (Neuphonic, Oct 2025) |
| **Watermarking** | ✅ Perth watermark built-in |
| **Inference** | llama.cpp / llama-cpp-python (CPU) |

## Strengths

- **Apache 2.0** — commercial use, no royalties
- **Sub-1B params, CPU-only** — most efficient SOTA-quality engine
- **GGUF Q4/Q8 quantizations** — fits on Raspberry Pi, phones, edge devices
- **3-second voice cloning** with realistic quality
- **Perth watermarking** — only OSS TTS with built-in content traceability
- **Qwen 0.5B backbone** — leverages Qwen's text understanding
- **No GPU required** — democratizes local TTS to low-end hardware
- **Compliance-friendly** — Perth watermark satisfies EU AI Act traceability requirements

## Weaknesses

- **English only** — no multilingual support
- **Q4 quantization = quality loss** vs. fp16 alternatives
- **NeuCodec is proprietary** — codec weights are part of the Apache release but format is Neuphonic-specific (lock-in risk)
- **Single-speaker focus** — no multi-speaker dialogue like Dia
- **Newer ecosystem** (Oct 2025) — community ports and integrations still building
- **Perth watermark = can't strip it** — content is traceable (feature for some, bug for others)

## Mery integration notes

NeuTTS Air is the **on-device champion** for Mery's P1 priority "scale to 10 languages" — specifically for English-quality voice cloning on consumer hardware. Use cases:

1. **Voice cloning on low-end devices** — Raspi, old laptops, phones
2. **Compliance / EU AI Act** — Perth watermark is a built-in audit trail
3. **English quality on edge** — better than piper-plus for voice cloning, similar footprint
4. **Qwen ecosystem alignment** — if Mery integrates Qwen for text, NeuTTS Air reuses the same family

Critical gap: **English only**. Doesn't help Vietnamese or multilingual strategy. Best paired with:
- **Supertonic** for Vietnamese + 30 other langs (on-device)
- **Qwen3-TTS** for 10 langs with voice cloning (GPU)
- **MeloTTS-Vietnamese** for Vietnamese-specific quality (CPU)

## Watermarking

Perth is Neuphonic's neural watermarking scheme, baked into NeuCodec output:
- **Inaudible to humans** — embedded in audio bitstream
- **Detectable with Perth decoder** — proves audio was NeuTTS-generated
- **Compliance use cases** — EU AI Act Art. 50 (transparency), US state deepfake laws
- **Mery governance axis** — `axes/05-governance-and-licensing.md` already flags this need

## Reference

- [neuphonic/neutts-air HuggingFace](https://huggingface.co/neuphonic/neutts-air) — model card + Q4/Q8 GGUF
- [neuphonic/neutts-air GitHub](https://github.com/neuphonic/neutts-air) — main repo
- [neuphonic.com](https://neuphonic.com/) — official site
- [KiaDev release coverage](https://kiadev.net/news/2025-10-03-neutts-air-748m-on-device-voice-cloning) — Oct 2025

## Engine × tier classification

| Sub-item | NeuTTS Air |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ (24kHz WAV) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (real-time) |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | Tier 3 ✅ (3–15s zero-shot) |
| Watermarking | Tier 3 ✅ (Perth built-in) |
| SSML | Tier 3 (not supported) |
| Multilingual | English only |
| Vietnamese | ❌ |
| On-device | ✅ (Raspberry Pi, phone, laptop) |
| GPU required | ❌ (CPU-only) |
| Edge-ready | ✅ |

## Decision status

🟢 **Strong future candidate** for Mery's on-device English voice cloning. Beats Chatterbox-Turbo on footprint (no GPU), beats piper-plus on cloning quality, adds watermarking for governance.

## Strategic fit

For Mery's "Voice cloning" axis (P1/P2), NeuTTS Air is the **on-device quality leader** for English. Combined with:
- **Supertonic** (on-device multilingual, 31 langs)
- **Qwen3-TTS** (GPU, 10 langs, voice cloning)
- **MeloTTS-Vietnamese** (CPU, Vietnamese-specific)

…Mery gets full coverage: edge to GPU, English to 600 languages, no-cloning to high-quality cloning, with watermarking for compliance.
