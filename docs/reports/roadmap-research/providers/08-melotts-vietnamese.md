# Provider 08 — MeloTTS-Vietnamese

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (Vietnamese path)

---

## Overview

MeloTTS-Vietnamese is a community fine-tune of MyShell's MeloTTS for Vietnamese. Uses 45 phonemes + 8 tones, integrates PhoBERT for linguistic features and underthesea for text segmentation. MIT-licensed.

## Specifications

| Attribute | Value |
|---|---|
| **License** | MIT (community fine-tune) |
| **Languages** | Vietnamese (specialized) |
| **Vietnamese** | ✅ **Native** |
| **Voice cloning** | ❌ (synthesis-only) |
| **Streaming** | ✅ (real-time on CPU) |
| **Model size** | ~? (MeloTTS base ~250-500MB + VI fine-tune) |
| **Latency P50** | Real-time on CPU |
| **Hardware** | CPU (best), CUDA |
| **Quantization** | fp16, int8 |
| **Maintenance** | Limited (Dec 2024 last update on base MeloTTS) |
| **Adoption signals** | HuggingFace, used in some VI accessibility projects |

## Strengths

- **Vietnamese native** — most important for Mery's creator (Vietnamese teacher)
- **MIT license** — fully commercial-safe
- **CPU-friendly** — real-time on CPU
- **Custom VI G2P** — 45 phonemes, 8 tones, proper diacritics handling
- **PhoBERT integration** — state-of-the-art VI linguistic features
- **underthesea integration** — proven VI NLP toolkit

## Weaknesses

- **Single language** — Vietnamese only
- **No voice cloning** — synthesis-only
- **Limited maintenance** — base MeloTTS last updated Dec 2024
- **Small community** — VI fine-tunes are niche
- **No word timing** — would need external alignment
- **Quality vs Fish Audio S2** — Fish Audio S2 is larger but higher quality

## Vietnamese-specific technical details

- **Phonemes:** 45 (covers all 8 tones × vowel patterns)
- **Text segmentation:** underthesea word/sentence tokenizer
- **Linguistic features:** PhoBERT embeddings
- **Tone handling:** proper diacritic preservation
- **NFC normalization:** required (Vietnamese diacritics critical)

## Mery integration notes

**This is Mery's "Vietnamese path" if Fish Audio S2 is rejected for license reasons.**

Integration approach:
- Fork or wrapper: Mery adapter wraps `MeloTTS_Vietnamese` package
- Vietnamese-first: Mery's default engine for VI text could be this
- Could ship as a separate Mery extension: `mery-tts-vi` package
- Maintenance: would need ongoing VI NLP updates (underthesea, PhoBERT evolution)

**Trade-off:**
- MeloTTS-Vietnamese: full control, MIT, but maintenance burden
- Fish Audio S2: zero maintenance, but Research License

**Recommendation:** If Mery commits to VI as a core feature, **fine-tune MeloTTS-Vietnamese** and ship as bundled engine. This is the long-term play.

## Reference

- [manhcuong02/MeloTTS_Vietnamese](https://github.com/manhcuong02/MeloTTS_Vietnamese) — main repo
- [MeloTTS base](https://github.com/myshell-ai/melotts) — original MyShell repo
- [underthesea](https://github.com/undertheseanlp/underthesea) — VI NLP toolkit
- [PhoBERT](https://github.com/VinAIResearch/PhoBERT) — VI BERT
- [nmcuong/MeloTTS-Vietnamese](https://huggingface.co/nmcuong/MeloTTS-Vietnamese) — HF model
- [MeloTTS-Vietnamese Infore dataset](https://github.com/) — 25hr training data

## Engine × tier classification

| Sub-item | MeloTTS-Vietnamese |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 ❌ |
| Voice cloning | Tier 3 ❌ (synthesis only) |
| SSML | Tier 3 ❌ |
| Multilingual | Vietnamese only |
| Vietnamese | ✅ **Native** |

## Decision status

🎯 **P3 candidate for Vietnamese path (alternative to Fish Audio S2).** Best if Mery wants full VI control + MIT license + accepts maintenance burden.

## Training data note

The community fine-tune uses the **Infore dataset** (25 hours). This is the same dataset used by many VI TTS research projects. License: needs verification (some VI datasets have non-commercial restrictions). **Verify before bundling.**
