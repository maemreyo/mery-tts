# Provider 14 — Orpheus TTS (Canopy Labs)

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (LLM-based, Apache 2.0)

---

## Overview

**Orpheus TTS** is Canopy Labs' LLM-based TTS, built on the Llama-3b backbone. Released March 2025 with multilingual research preview April 2025, Orpheus is one of the first production-grade TTS systems demonstrating that the "LLM-for-speech" paradigm can match specialized TTS architectures. Comes in 4 sizes (3B/1B/400M/150M) for different deployment targets, all under Apache 2.0.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | English (GA); multilingual research preview (8+ langs) |
| **Vietnamese** | ❌ (not in research preview set) |
| **Voice cloning** | ✅ Zero-shot, no fine-tuning required |
| **Streaming** | ✅ (~200ms; reducible to ~100ms with input streaming) |
| **Model size** | 3B / 1B / 400M / 150M (4 variants) |
| **Latency P50** | 200ms default; 100ms with input streaming |
| **Hardware** | fp8 (Baseten optimized) or fp16 (full fidelity); GPU required for 3B |
| **Sample rate** | 24kHz |
| **Quantization** | fp8 / fp16 / int8 |
| **Maintenance** | Active (Canopy Labs, partner with Baseten for inference) |
| **Architecture** | Llama-3b backbone adapted for speech tokens |

## Strengths

- **Apache 2.0** — fully commercial-safe, patent grant
- **LLM-based architecture** — can leverage LLM tooling (vLLM, FlashAttention, etc.)
- **4 model sizes** — 150M for edge, 3B for quality; granular deployment choice
- **Low latency** — 100–200ms streaming with sub-200ms practical
- **Multilingual research preview** — covers EN, ES, FR, DE, IT, PT, ZH, JA
- **Guided emotion tags** — control speech emotion with simple inline tags
- **Backed by Baseten** for optimized fp8 inference — production-grade serving path
- **6.2K GitHub stars** — active community

## Weaknesses

- **LLM inference stack** — heavier than purpose-built TTS (needs vLLM/similar)
- **GPU required** for 3B/1B; 400M/150M can run on CPU but with quality tradeoffs
- **No Vietnamese** in current research preview
- **Newer ecosystem** — fewer production deployments than Kokoro/XTTS
- **Quality ceiling** — LLM-based but still trails specialized diffusion models (F5-TTS) on naturalness benchmarks

## Mery integration notes

Orpheus is the **most LLM-native TTS** in the candidate set. Implications for Mery:

1. **Reuses LLM serving infrastructure** — if Mery already runs vLLM for any LLM, Orpheus drops in
2. **fp8 inference path** with Baseten — same operational profile as LLM serving
3. **4 model sizes** — supports "edge" (150M) to "quality" (3B) spectrum

For Mery's LLM-ecosystem integration (e.g., a future "Ollama for TTS" + LLM tool), Orpheus fits naturally. For lightweight desktop TTS, Kokoro/Supertonic remain better picks.

## Voice cloning details

| Aspect | Spec |
|---|---|
| Reference length | ~10 seconds |
| Zero-shot | ✅ (no fine-tuning) |
| Emotion tags | `<laugh>`, `<sigh>`, etc. inline |
| Cross-lingual | Research preview only |
| Fine-tuning | Provided scripts + sample datasets |

## Reference

- [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS) — main repo
- [canopylabs/orpheus-tts-0.1-finetune-prod](https://huggingface.co/canopylabs/orpheus-tts-0.1-finetune-prod) — finetuned model
- [canopylabs/orpheus-multilingual-research-release](https://huggingface.co/collections/canopylabs/orpheus-multilingual-research-release-67f5894cd16794db163786ba) — multilingual research
- [Baseten blog](https://www.baseten.co/blog/canopy-labs-selects-baseten-as-preferred-inference-provider-for-orpheus-tts-model) — fp8 inference partnership

## Engine × tier classification

| Sub-item | Orpheus |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ (24kHz) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (100–200ms) |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | Tier 3 ✅ (zero-shot, ~10s) |
| Emotion tags | Tier 3 ✅ (inline) |
| SSML | Tier 3 (tags, not full SSML) |
| Multilingual | EN + 8 research preview |
| Vietnamese | ❌ |
| LLM ecosystem | ✅ (vLLM, FlashAttention) |
| GPU required | ⚠️ Yes for quality variants |

## Decision status

🟡 **Strategic future candidate** for Mery's "TTS in the LLM ecosystem" axis. Not a near-term pick because:
- Kokoro/Supertonic are faster for lightweight English/multilingual
- Vietnamese not yet supported
- LLM serving infrastructure is heavier than purpose-built TTS

But worth tracking as LLM-tooling TTS becomes the norm (2026 trend).

## Strategic fit

If Mery's roadmap adds **"run alongside local LLM"** integration (e.g., LLM-generated response → Mery voice output in one local pipeline), Orpheus is the cleanest fit. For pure TTS, Kokoro/Supertonic still win on speed and footprint.
