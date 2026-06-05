# Provider 10 — RVC (Retrieval-based Voice Conversion)

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (voice conversion only — different category)

---

## Overview

RVC is the de facto open-source voice conversion tool. It takes a source voice and converts it to a target voice while preserving prosody. Used heavily for song covers, voice acting, and character voice. **RVC is voice CONVERSION, not TTS** — important distinction.

## Specifications

| Attribute | Value |
|---|---|
| **License** | MIT |
| **Languages** | Any (via TTS pipeline → RVC conversion) |
| **Vietnamese** | ✅ via pipeline |
| **Voice cloning** | ✅ (fine-tuning, 10min data minimum) |
| **Streaming** | ✅ (real-time, 90-170ms) |
| **Model size** | VITS-based, ~200-500MB per voice |
| **Latency P50** | 90-170ms (real-time) |
| **Hardware** | CPU, CUDA (best) |
| **Quantization** | fp16, int8 |
| **Maintenance** | Active (36K GitHub stars, "Ultimate RVC" fork) |
| **Adoption signals** | Massive community, 100K+ voice models shared |

## Strengths

- **MIT license** — commercial-safe
- **Real-time capable** — 90-170ms latency
- **Massive community** — 100K+ voice models in circulation
- **Any language** — operates on audio, language-agnostic
- **Fine-tuning** — 10min data is enough for high quality

## Weaknesses

- **Voice conversion, not TTS** — needs source audio from somewhere (TTS engine)
- **Top-1 retrieval to prevent timbre leakage** — complexity
- **Copyright concerns** — community often clones without consent
- **Pipeline complexity** — RVC + TTS engine = extra hop
- **No word timing** — operates post-TTS, so timing already lost
- **Prosody preservation** — works well but not perfect

## Voice cloning capability

- **Type:** Fine-tuning (10min data minimum) — heaviest of all engines
- **Cross-lingual:** ✅ Language-agnostic
- **Quality:** High (community-rated)
- **Vietnamese cloning:** ✅ (if source TTS supports VI)

## Mery integration notes

RVC is a **different category** from the other engines. Mery's current architecture is TTS-only (text → audio). RVC is voice conversion (audio → audio). To use RVC, Mery would need:

1. Run a TTS engine first (piper-plus, Kokoro) to get source audio
2. Run RVC on that source audio to convert to target voice
3. Return converted audio

This is a **2-hop pipeline** that adds latency but enables unlimited voice cloning.

**When to consider RVC:**
- Voice cloning axis (P3, gated by governance)
- After OpenVoice v2 or F5-TTS prove insufficient
- For specific use cases like song covers, character voice

**When NOT to use RVC:**
- Default voice cloning path (overkill, use OpenVoice v2 first)
- Real-time voice (latency too high for 2-hop)
- Without governance framework (community has consent issues)

## Reference

- [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) — main repo
- [Ultimate RVC](https://github.com/) — active fork with improvements
- [RVC docs](https://docs.rvc.fans/) — community documentation

## Engine × tier classification

| Sub-item | RVC |
|---|---|
| Synthesize | N/A (voice conversion, not TTS) |
| Voice selection | N/A (target voice) |
| Output format | Tier 1 BASE ✅ |
| Speed control | N/A |
| Streaming | Tier 2 COMMON ✅ (real-time) |
| Word timing | N/A (post-TTS) |
| Voice cloning | Tier 2 COMMON ✅ (fine-tune, 10min data) |
| SSML | N/A |
| Multilingual | Any (language-agnostic) |
| Vietnamese | ✅ via pipeline |

## Decision status

🎯 **P3+ future candidate, only after voice cloning axis is active.** Different category from TTS engines. Consider when community cloning needs are beyond zero-shot capabilities.

## Governance warning

RVC community has a **copyright/consent problem** — many shared voices are cloned without consent. Mery should not blindly adopt RVC's community catalog. See `axes/05-governance-and-licensing.md`.
