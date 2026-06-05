# Provider 04 — F5-TTS

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (not active)

---

## Overview

F5-TTS is a flow-matching based TTS with strong zero-shot voice cloning. Code is MIT-licensed; model weights are CC-BY-NC-4.0 (non-commercial). It's a popular research/quality benchmark in the open-source TTS community.

## Specifications

| Attribute | Value |
|---|---|
| **License (code)** | MIT |
| **License (weights)** | CC-BY-NC-4.0 (non-commercial) |
| **Languages** | EN, ZH (base) + community ports |
| **Vietnamese** | ❌ (community fine-tunes only) |
| **Voice cloning** | ✅ 5-15s reference (zero-shot) |
| **Streaming** | ✅ (chunked) |
| **Model size** | ~1B parameters (~3.5GB fp16) |
| **Latency P50** | ~300-500ms (CPU/GPU) |
| **Hardware** | CPU, CUDA |
| **Quantization** | fp16 (limited int8) |
| **Maintenance** | Active (14.6K GitHub stars) |
| **Adoption signals** | Strong research community, multiple forks |

## Strengths

- **High quality cloning** — MOS 4.3 (best among open-source zero-shot)
- **MIT code** — usable in commercial Mery integration
- **Active research** — multiple improvements in 2025-2026
- **Flow matching** — modern architecture, better than transformer-based

## Weaknesses

- **Non-commercial weights** — CC-BY-NC means Mery cannot distribute weights commercially
- **No Vietnamese** — base is EN/ZH only
- **Large model** — ~1B parameters
- **Slower than real-time on CPU** — needs GPU for production
- **Code requires GPU** — CPU path exists but is slow

## Voice cloning capability

- **Type:** Zero-shot, 5-15s reference audio
- **Cross-lingual:** ✅ (with community ports)
- **Quality:** MOS 4.3 (SOTA for open-source zero-shot)
- **Vietnamese cloning:** Possible only with community fine-tune

## Mery integration notes

If Mery adds F5-TTS:
- **License issue:** Weights are CC-BY-NC, so Mery cannot bundle them in PyPI package
- **Solution:** F5-TTS model downloaded on-demand by user (not bundled)
- Optional dependency: `f5-tts>=1.0` (MIT, installable)
- Python API: `from f5_tts.api import F5TTS` or subprocess
- Hardware: NVIDIA GPU strongly recommended

**This is the model ElevenLabs-killer research projects point to**, but the license prevents commercial use of the weights. Mery can:
- ✅ Provide F5-TTS as an opt-in adapter (user downloads weights themselves)
- ❌ Cannot bundle F5-TTS weights in `mery-tts-server` PyPI package

## Reference

- [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) — main repo
- [F5-TTS paper](https://arxiv.org/abs/2410.06885) — flow matching architecture
- [F5-TTS HuggingFace](https://huggingface.co/SWivid/F5-TTS) — model weights

## Engine × tier classification

| Sub-item | F5-TTS |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 (partial) |
| Voice cloning | Tier 2 COMMON ✅ (5-15s ref) |
| SSML | Tier 3 ❌ |
| Multilingual | EN, ZH (base) |
| Vietnamese | ❌ (community only) |

## Decision status

⚠️ **P3 future candidate.** MIT code allows Mery integration, but CC-BY-NC weights prevent bundling. Add as opt-in adapter if user demand exists.
