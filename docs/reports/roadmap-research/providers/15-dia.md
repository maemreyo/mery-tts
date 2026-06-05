# Provider 15 — Dia / Dia2 (Nari Labs)

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (multi-speaker dialogue)

---

## Overview

**Dia** is Nari Labs' open-source dialogue TTS, released April 2025, designed for multi-speaker conversational audio. The **Dia2** update extends to even more natural dialogue patterns. Built on a 1.6B-parameter foundation model, Dia generates both speech and non-verbal vocalizations (laughs, sighs, breaths) from a chat-style script using speaker tags like `[S1]` and `[S2]`. Apache 2.0 licensed.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | English only |
| **Vietnamese** | ❌ |
| **Voice cloning** | ❌ (preset speakers only) |
| **Streaming** | ✅ |
| **Model size** | 1.6B parameters |
| **Latency P50** | Medium (not optimized for real-time; designed for offline dialogue generation) |
| **Hardware** | GPU strongly recommended (8GB+ VRAM) |
| **Sample rate** | 44.1kHz |
| **Quantization** | fp16 standard |
| **Maintenance** | Active (Nari Labs community, Dia2 in development) |
| **Architecture** | Discrete codec + LM hybrid (similar to VALL-E X pattern) |

## Strengths

- **Apache 2.0** — fully commercial-safe
- **Multi-speaker dialogue** as a first-class use case (vs. single-speaker monologue)
- **Non-verbal vocalizations** — laughs, sighs, breaths, coughs, etc. inline
- **Speaker tags** — `[S1]`, `[S2]` for script-style multi-voice content
- **High quality audio** at 44.1kHz
- **Different niche** from Kokoro/piper — designed for audiobooks/podcasts/dialogue
- **Community** — popular in audio-storytelling and accessibility spaces

## Weaknesses

- **English only** — no multilingual support
- **No voice cloning** — preset speakers only (limits personalization)
- **GPU-heavy** (1.6B params + 8GB+ VRAM) — not a consumer-laptop engine
- **Slower** than real-time-first engines like Supertonic/Kokoro
- **Specialized use case** — overkill for short single-voice TTS

## Mery integration notes

Dia fills a **specific niche** that Mery's current engines (piper-plus, Kokoro) don't cover: multi-speaker dialogue generation. Use cases for Mery:

1. **Audiobook generation** — multi-character narration
2. **Dialogue content** — interviews, podcasts, conversational content
3. **Accessibility** — read dialogue-heavy content (e.g., screenplays, comics)

But Dia is **not a replacement for Kokoro/piper** for everyday TTS. It's a **specialized "long-form dialogue" engine** that complements the lightweight engines.

Risks:
- **Single-vendor (Nari Labs)** — no major company backing; long-term sustainability unknown
- **English-only** — doesn't help Vietnamese strategy

## Reference

- [nari-labs/dia](https://github.com/nari-labs/dia) — main repo
- [Dia on HuggingFace](https://huggingface.co/nari-labs/Dia-1.6B) — model weights
- [waydegilliam/dia-modal](https://github.com/waydegilliam/dia-modal) — Modal deployment
- [Modal blog — open-source TTS](https://modal.com/blog/open-source-tts) — listed in 2025 top engines

## Engine × tier classification

| Sub-item | Dia |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ (preset speakers) |
| Output format | Tier 1 BASE ✅ (44.1kHz) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | ❌ |
| Multi-speaker | ✅ (Tier 3 specialty) |
| Non-verbal tags | ✅ (Tier 3 specialty) |
| SSML | Tier 3 (inline tags) |
| Multilingual | English only |
| Vietnamese | ❌ |
| Dialogue generation | ✅ (unique strength) |
| GPU required | ✅ (8GB+) |

## Decision status

🟡 **Niche future candidate** for Mery's "long-form dialogue" use case. Not on the critical path for daily TTS, but worth adding when Mery's content scope expands to audiobooks/podcasts.

## Strategic fit

Dia doesn't compete with Kokoro/piper on single-voice low-latency TTS. It competes in a **different category** — multi-speaker dialogue generation. If Mery's users ask for "narrate this screenplay" or "generate a podcast from this conversation," Dia is the answer. Otherwise, keep on watchlist.
