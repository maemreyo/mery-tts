# Provider 09 — ChatTTS

**Last updated:** 2026-06-05
**Status in Mery:** Not recommended (license issues)

---

## Overview

ChatTTS is a 300M-parameter TTS designed for dialogue/conversational use cases, with token-level emotion control (e.g., `[laugh]`, `[uv_break]`, `[oral_0-9]`, `[speed_0-9]`). High adoption (39K stars) but **AGPL-3.0 code + CC-BY-NC-4.0 weights** create license friction.

## Specifications

| Attribute | Value |
|---|---|
| **License (code)** | AGPL-3.0 (viral, network copyleft) |
| **License (weights)** | CC-BY-NC-4.0 (non-commercial) |
| **Languages** | EN, ZH |
| **Vietnamese** | ❌ |
| **Voice cloning** | ❌ |
| **Streaming** | ✅ (RTF ~0.3) |
| **Model size** | 300M (~1GB fp16) |
| **Latency P50** | ~300ms |
| **Hardware** | CPU, CUDA |
| **Maintenance** | Active (39K GitHub stars) |
| **Adoption signals** | Trending research, used in some LLM voice projects |

## Strengths

- **Emotion tokens** — `[laugh]`, `[uv_break]`, `[oral_0-9]`, `[speed_0-9]` for expressive speech
- **Designed for LLM** — natural fit for LLM-voice use case
- **Active community** — 39K stars
- **Streaming** — RTF 0.3, real-time capable

## Weaknesses

- **AGPL-3.0 code** — viral copyleft; if Mery links AGPL code, Mery must be AGPL
- **CC-BY-NC-4.0 weights** — non-commercial only
- **No Vietnamese** — EN/ZH only
- **No voice cloning** — fixed voices
- **No word timing** — would need external alignment

## Why NOT recommended for Mery

**AGPL-3.0 is a deal-breaker for Mery's distribution model.** AGPL requires that any network service using AGPL code must also be AGPL-licensed. This would force Mery's entire codebase to be AGPL, which conflicts with the GPLv3 license already on the repo (per README) and would prevent commercial use.

Mery's current license (per `README.md` line 152): **GPLv3**. AGPL is even more restrictive (viral + network clause).

**Decision: Do not integrate ChatTTS into Mery.**

## Reference (for completeness, not for integration)

- [2noise/ChatTTS](https://github.com/2noise/ChatTTS) — main repo
- [ChatTTS HuggingFace](https://huggingface.co/2Noise/ChatTTS) — model
- [AGPL-3.0 license text](https://www.gnu.org/licenses/agpl-3.0.html) — license terms

## Engine × tier classification

| Sub-item | ChatTTS |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 ❌ |
| Voice cloning | Tier 3 ❌ |
| SSML | Tier 3 (custom tokens) |
| Multilingual | EN, ZH |
| Vietnamese | ❌ |

## Decision status

❌ **DO NOT INTEGRATE.** AGPL-3.0 + CC-BY-NC-4.0 weights = incompatible with Mery's GPLv3 + commercial goals.
