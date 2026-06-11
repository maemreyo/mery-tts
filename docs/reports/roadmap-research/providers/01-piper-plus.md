# Provider 01 — piper-plus

**Last updated:** 2026-06-05
**Status in Mery:** Current (ADR-0004)

---

## Overview

piper-plus is a fork of Piper (the original Piper-TTS was GPL-3.0; piper-plus is MIT). It's a fast, lightweight neural TTS optimized for CPU inference, with added speaker embedding support for zero-shot voice cloning and phoneme timing output.

## Specifications

| Attribute | Value |
|---|---|
| **License** | MIT (piper-plus), GPL-3.0 (original Piper) |
| **Languages** | 8 (EN/JA/ZH/KO/ES/FR/PT/SV) |
| **Vietnamese** | ❌ (custom G2P needed) |
| **Voice cloning** | ✅ via speaker embedding (zero-shot) |
| **Streaming** | ✅ (chunked output) |
| **Model size** | ~20-75MB per voice (MB-iSTFT: 20MB, medium: 65MB) |
| **Latency P50** | ~38ms (MB-iSTFT), 27ms on ANE |
| **Hardware** | CPU (best), CUDA, DirectML, ANE (with refactor) |
| **Quantization** | fp16, int8 (palettized for ANE) |
| **Maintenance** | Active |
| **Adoption signals** | 164+ GitHub stars, used as Mery's "lightweight" engine per ADR-0004 |

## Strengths

- **MIT license** — commercially safe, no GPL contamination
- **CPU-first** — runs on any machine without GPU (key for Mery's "install anywhere" mission)
- **Phoneme timing** — built-in JSON/TSV/SRT output, perfect for word timing axis
- **Multi-language** — 8 languages, reasonable coverage
- **Small models** — 20-75MB per voice, manageable download
- **Mature runtime** — Python API via `piper-plus` package

## Weaknesses

- **Vietnamese not native** — would need custom espeak-ng G2P or character-based synthesis
- **Quality ceiling** — "lightweight" category, Kokoro is better for natural listening
- **Streaming quirk** — chunked, not true real-time (some delay before first chunk)
- **License mismatch with original Piper** — piper-plus forked specifically to escape GPL, so ecosystem docs reference both

## Mery integration notes

ADR-0004 chose piper-plus as Mery's lightweight engine. Key integration points:
- Package: `piper-plus>=1.10.0` (optional dependency in pyproject.toml)
- Python API: `piper_plus.PiperPlus(onnx_path)` directly (no subprocess per Grill Q1)
- Entry point: `mery_tts.engines` group → `mery_tts.engines.piper_plus.adapter:PiperPlusAdapter`
- Phonation: streaming via async iterator bridge (per ARCHITECTURE.md)
- Word timing: built-in via `--phoneme-timing` flag, expose as `word.boundary` WS event (P1)

## Voice cloning in piper-plus

- **Type:** Speaker embedding (zero-shot)
- **Reference:** Any audio file with single speaker
- **Output:** ONNX model that can synthesize in the embedded voice
- **Quality:** Medium (per Grill Q1 evaluation)
- **Vietnamese voice cloning:** Possible if custom G2P is integrated

## Reference

- [piper-plus GitHub](https://github.com/ayutaz/piper-plus) — MIT fork
- [OHF-Voice piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) — original GPL version
- [Piper voices on HuggingFace](https://huggingface.co/rhasspy/piper-voices) — model collection
- [Piper SSML issue #275](https://github.com/rhasspy/piper/issues/275) — limited SSML support

## Engine × tier classification

| Sub-item | piper-plus |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format (PCM, WAV) | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ (via duration scale) |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 2 COMMON ✅ (built-in) |
| Voice cloning | Tier 3 ✅ (zero-shot) |
| SSML | Tier 3 ❌ (limited) |
| Multilingual | 8 langs |
| Vietnamese | ❌ |

## Decision status

✅ Active in Mery (ADR-0004). No migration needed.
