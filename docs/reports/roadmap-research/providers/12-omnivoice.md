# Provider 12 — OmniVoice

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (broadest language coverage)

---

## Overview

**OmniVoice** is a massively multilingual zero-shot TTS model from Xiaomi's next-generation Kaldi team (k2-fsa), released April 2026. It supports **over 600 languages and dialects** — the broadest coverage of any open-source TTS — using a novel diffusion language model (NAR) architecture. Built on Qwen3-0.6B text encoder with AudioVAE-style audio modeling, trained on 581k hours of curated open-source speech data.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | 600+ (broadest of any open-source TTS) |
| **Vietnamese** | ✅ (one of 600+, ISO 639-3: `vie`) |
| **Voice cloning** | ✅ Zero-shot from 3–25s reference audio |
| **Voice design** | ✅ Describe voice in natural language (gender, age, pitch, accent, whisper) |
| **Streaming** | ❌ (no first-class streaming API yet) |
| **Model size** | ~0.5–1B parameters (Qwen3-0.6B + audio decoder) |
| **Latency P50** | RTF 0.025 (40× real-time) on GPU; A6000-grade hardware recommended |
| **Hardware** | NVIDIA GPU (CUDA), Apple Silicon (Metal), CPU (slower) |
| **Sample rate** | 24kHz WAV |
| **Quantization** | bf16/fp16 standard |
| **Maintenance** | Active (Xiaomi k2-fsa team, April 2026 release) |
| **Framework** | PyTorch + JAX (dual backend) |
| **Non-verbal control** | `[laughter]`, `[sigh]`, etc. + pinyin/phoneme pronunciation correction |

## Strengths

- **600+ languages** — covers low-resource languages no other TTS supports
- **Apache 2.0** with explicit commercial use grant
- **Voice cloning + Voice design** — two modes in one model
- **40× real-time** on GPU — production throughput
- **2.85% WER** on 24-language benchmark (vs. ElevenLabs 10.95%)
- **Qwen3 backbone** — strong text understanding for normalization
- **Cross-lingual cloning** — clone English voice, speak Vietnamese
- **581k training hours** — most open training data of any TTS

## Weaknesses

- **GPU-heavy** — needs A6000-class hardware for 40× RTF; CPU not viable for production
- **No streaming API** — blocking inference only (limits real-time agent use)
- **Largest model footprint** — bigger than Kokoro/Supertonic by an order of magnitude
- **Self-reported benchmarks** — independent validation sparse (April 2026 release)
- **Voice cloning on 600 langs = average quality** per language vs. narrow specialists

## Mery integration notes

OmniVoice is the **only 2026 open-source model covering 600+ languages** with a permissive license. Mery-relevant scenarios:

1. **Universal fallback engine** — if user request language is not in piper-plus/Kokoro/MeloTTS-VI's repertoire, OmniVoice handles it
2. **Vietnamese option #2** — alongside MeloTTS-Vietnamese, for users wanting Qwen-quality text normalization
3. **Long-tail language strategy** — Zam Reader roadmap could expand beyond English+VI

Cost vs. benefit for Mery:
- **Pro:** Single engine replaces 5+ narrow specialists
- **Con:** 8GB+ VRAM requirement excludes Mery's "runs on consumer laptops" positioning

## Voice cloning details

| Aspect | Spec |
|---|---|
| Reference length | 3–25 seconds |
| Cross-lingual | ✅ (English ref → VI/JA/KO output preserves timbre) |
| Continuation mode | ✅ (append to existing audio, like voice-actor narration) |
| Quality vs. ElevenLabs | 0.830 vs. 0.655 speaker similarity (independent benchmark) |
| Storage per clone | ~1MB embedding vector |

## Reference

- [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) — main repo
- [k2-fsa/OmniVoice on HuggingFace](https://huggingface.co/k2-fsa/OmniVoice) — model weights (Apache 2.0)
- [arxiv 2604.00688](https://arxiv.org/abs/2604.00688) — paper
- [OmniVoice demo](https://zhu-han.github.io/omnivoice) — official sample page
- [OmniVoice HuggingFace Space](https://huggingface.co/spaces/k2-fsa/OmniVoice) — try in browser

## Engine × tier classification

| Sub-item | OmniVoice |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ (24kHz WAV) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | ❌ (Tier 3 gap) |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | Tier 3 ✅ (zero-shot, 3–25s) |
| Voice design | Tier 3 ✅ (text-prompted) |
| SSML | Tier 3 (pronunciation correction only) |
| Multilingual | 600+ langs |
| Vietnamese | ✅ Native (with `vie` ISO code) |
| Non-verbal tags | ✅ (`[laughter]`, etc.) |
| GPU required | ✅ (CPU not viable) |

## Decision status

🟡 **Strategic future candidate.** Not a near-term pick for Mery (GPU requirement, no streaming), but a strong **"universal fallback"** option if/when Mery opens up to languages beyond English+VI.

## Strategic fit

If Mery's mission is "Ollama for TTS" — universal local inference — then OmniVoice is the **best single engine for the "long tail" of languages**. But Mery's current positioning (consumer-laptop friendly, streaming-first) makes Kokoro/Supertonic better near-term picks. OmniVoice fits the "scale to 100+ languages" axis once governance and ops scale.
