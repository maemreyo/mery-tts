# Provider 13 — Chatterbox (Resemble AI)

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (English voice cloning + emotion control)

---

## Overview

**Chatterbox** is Resemble AI's open-source voice cloning TTS, released May 2025, that beat ElevenLabs in blind preference tests. The **Chatterbox-Turbo** variant (2026) brings sub-200ms latency and 4–8GB VRAM footprint, making it the first open-source clone to credibly compete with commercial voice cloning APIs on quality. Built-in emotion exaggeration control and paralinguistic tags (`[laugh]`, `[cough]`, `[chuckle]`) are first-class features.

## Specifications

| Attribute | Value |
|---|---|
| **License** | MIT (commercial-safe) |
| **Languages** | English primary; multilingual in research preview |
| **Vietnamese** | ❌ (English-centric in GA) |
| **Voice cloning** | ✅ Zero-shot from 5–10s reference audio |
| **Streaming** | ✅ (Turbo variant) |
| **Model size** | 350M params (Turbo); full model larger |
| **Latency P50** | Sub-200ms (Turbo) |
| **Hardware** | 4–8GB VRAM (Turbo); full model needs more |
| **Sample rate** | 24kHz |
| **Quantization** | fp16 standard |
| **Maintenance** | Active (Resemble AI, MIT-licensed) |
| **Key feature** | Emotion exaggeration control (dial 0.0–1.0) |

## Strengths

- **63.75% preference rate vs. ElevenLabs** in blind A/B tests (the headline number)
- **MIT licensed** — commercial use, no royalties
- **5–10s reference** for cloning — shorter than XTTS-v2 (3s minimum but quality drops)
- **Emotion control** as a first-class parameter (no prompt engineering)
- **Paralinguistic tags** baked into the model (`[laugh]`, `[cough]`, `[chuckle]`, `[sigh]`)
- **Turbo variant** is small enough to run on consumer GPUs (4–8GB)
- **Resemble AI** — commercial company backing the OSS release (sustainability signal)

## Weaknesses

- **English-centric GA** — multilingual in research preview only
- **No Vietnamese** — unlike Supertonic, OmniVoice, Qwen3-TTS
- **Quality varies with reference audio quality** — bad ref → bad clone (true of all cloning models but Chatterbox is sensitive)
- **Newer ecosystem** — fewer community ports than XTTS-v2
- **Resemble AI may release a competing commercial product** — open-source commitment is a business decision that could change

## Mery integration notes

Chatterbox is the **English quality leader** among 2025–2026 open-source voice cloning models. For Mery:

1. **English voice cloning use case** — when a Zam Reader user wants "their own voice" reading English content, Chatterbox is the current best OSS option
2. **Replaces XTTS-v2 in priority matrix** — Chatterbox-Turbo has better latency + license (MIT) than XTTS-v2 (CPML ambiguous)
3. **Emotion control is novel** — no other Mery-candidate engine has first-class emotion parameter

Risks:
- **License change risk** — Resemble AI's commercial incentives could lead to re-licensing
- **English-only GA** — doesn't help with Vietnamese or multilingual expansion

## Voice cloning details

| Aspect | Spec |
|---|---|
| Reference length | 5–10 seconds recommended; 3s minimum |
| Emotion exaggeration | 0.0–2.0 parameter (1.0 = neutral, 2.0 = very expressive) |
| Paralinguistic tags | `[laugh]`, `[cough]`, `[chuckle]`, `[sigh]` (inline) |
| Cross-lingual | ❌ in GA |
| Storage per clone | ~few hundred MB embedding |

## Reference

- [ResembleAI/chatterbox-turbo](https://huggingface.co/ResembleAI/chatterbox-turbo) — HF model + spaces
- [Resemble AI blog](https://www.resemble.ai/) — release notes + commercial side
- [HuggingFace Spaces](https://huggingface.co/spaces/ResembleAI/Chatterbox) — try in browser
- SpeakEasy 2026 comparison: 5 engines that matter — [tryspeakeasy.io/blog/open-source-text-to-speech-2026](https://www.tryspeakeasy.io/blog/open-source-text-to-speech-2026)

## Engine × tier classification

| Sub-item | Chatterbox |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ (24kHz) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ (Turbo) |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | Tier 3 ✅ (5–10s zero-shot) |
| Emotion control | Tier 3 ✅ (first-class) |
| Paralinguistic tags | Tier 3 ✅ (inline `[laugh]` etc.) |
| SSML | Tier 3 (tags, not full SSML) |
| Multilingual | English primary |
| Vietnamese | ❌ |
| GPU required | ⚠️ Turbo on 4GB, full model more |

## Decision status

🟡 **Strong future candidate** for Mery's English voice cloning slot. Beats XTTS-v2 on:
- License clarity (MIT vs. CPML)
- Latency (sub-200ms Turbo)
- Quality (63.75% vs. ElevenLabs)

Recommended over XTTS-v2 in P1/P2 priority matrix. Watch for:
- Resemble AI re-licensing risk
- Multilingual GA timeline

## Strategic fit

For Mery's "Voice cloning" axis (currently mapped to OpenVoice v2 + RVC as fallback), Chatterbox-Turbo is the **best 2026 OSS option for English**. Combined with OpenVoice v2 (MIT, cross-lingual) and a Vietnamese engine (MeloTTS-VI or Supertonic), Chatterbox fills the "English quality" gap cleanly.
