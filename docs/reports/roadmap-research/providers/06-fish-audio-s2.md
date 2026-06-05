# Provider 06 — Fish Audio S2

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (multilingual expansion)

---

## Overview

Fish Audio S2 is a 4B-parameter LLM-based TTS with native support for 80+ languages including Vietnamese. SGLang backend provides ~100ms TTFA (Time To First Audio) for real-time streaming. License is "Fish Audio Research License" (non-standard, research use OK; commercial requires negotiation).

## Specifications

| Attribute | Value |
|---|---|
| **License** | Fish Audio Research License (research OK, commercial = negotiate) |
| **Languages** | **80+ including Vietnamese** |
| **Voice cloning** | ✅ 10-30s reference (zero-shot) |
| **Streaming** | ✅ SGLang, ~100ms TTFA, RTF 0.195 |
| **Model size** | 4B + 400M (~5GB total) |
| **Latency P50** | ~100ms TTFA (with SGLang) |
| **Hardware** | CUDA (best), CPU (slow) |
| **Quantization** | fp16, int8 |
| **Maintenance** | Active (31K GitHub stars) |
| **Adoption signals** | HuggingFace trending, used in commercial Fish Audio product |

## Strengths

- **80+ languages native** — most multilingual open-source TTS in 2026
- **Vietnamese native** — solves Mery's biggest gap
- **SOTA quality** — multiple leaderboard wins
- **Streaming** — SGLang backend enables ~100ms TTFA
- **Zero-shot cloning** — 10-30s reference, good quality
- **Word timing** — SGLang provides per-word timestamps
- **Multi-speaker** — `<|speaker:i|>` token for dialogue

## Weaknesses

- **License: Research only** — Fish Audio Research License requires commercial negotiation
- **Large model** — 5GB total, not a "lightweight" engine
- **GPU required** — CPU inference is too slow for real-time
- **Dependencies on SGLang** — extra infra for streaming
- **Closed training data** — don't know what's in the training set

## Voice cloning capability

- **Type:** Zero-shot, 10-30s reference
- **Cross-lingual:** ✅ Excellent
- **Quality:** SOTA on multiple benchmarks
- **Vietnamese cloning:** ✅ Native

## Mery integration notes

Fish Audio S2 is the **best candidate for Mery's multilingual expansion**, especially Vietnamese:
- Solves VI gap directly
- High quality matches "quality engine" category
- Streaming via SGLang complements Mery's WS protocol

**License path:**
- Research/personal use: ✅ OK
- Commercial: needs negotiation with Fish Audio
- Mery could ship as opt-in (user provides their own API key) or bundled if license is obtained

**If Mery commits to Vietnamese support:** Fish Audio S2 is faster path than fine-tuning MeloTTS-Vietnamese. But if VI is the only VI option, Mery becomes dependent on Fish Audio's roadmap.

## Reference

- [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) — main repo
- [Fish Audio](https://fish.audio/) — commercial product
- [MOSS-TTS-GGUF](https://huggingface.co/OpenMOSS-Team/MOSS-TTS-GGUF) — related Qwen3-based GGUF TTS
- [Fish Audio Research License](https://speech.fish.audio/) — license text

## Engine × tier classification

| Sub-item | Fish Audio S2 |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (SGLang, ~100ms TTFA) |
| Word timing | Tier 2 COMMON ✅ |
| Voice cloning | Tier 2 COMMON ✅ (10-30s ref) |
| SSML | Tier 3 ❌ |
| Multilingual | **80+ langs** |
| Vietnamese | ✅ Native |

## Decision status

🎯 **Target engine for Vietnamese + multilingual expansion (P2, license-gated).** If Fish Audio Research License terms are compatible, this is the fastest path. Otherwise, fine-tune MeloTTS-Vietnamese.
