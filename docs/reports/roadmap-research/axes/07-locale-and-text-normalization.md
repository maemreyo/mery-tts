# Axis 07 — Locale & Text Normalization (HIDDEN)

**Last updated:** 2026-06-05
**Status in roadmap:** **Not listed** — discovered via research
**Why it matters:** Especially for Vietnamese. If Mery reads "tiền" (money) as "ti-ên" (fairy), it's broken regardless of how good the engine is. This is **BASE correctness, not a feature**.

---

## What this axis covers

How Mery handles text before handing to the engine. Different engines have different normalization needs:
- UTF-8 canonical form (NFC vs NFD)
- Number → spoken form ("123" → "one hundred twenty-three")
- Date → spoken form ("2026-06-05" → "June fifth, twenty twenty-six")
- Currency ("$100" → "one hundred dollars")
- Abbreviations ("Dr." → "Doctor")
- URLs, emails (skip or speak char-by-char)
- Vietnamese diacritics (NFC critical)
- Engine-specific G2P (grapheme-to-phoneme)

## Unicode NFC vs NFD (critical for Vietnamese)

```python
import unicodedata

# NFC: precomposed (ề = U+1EC1)
text_nfc = "tiền"  # 4 chars, 1 codepoint for "ề"
# NFD: decomposed (e + combining circumflex + combining dot below)
text_nfd = "tie\u0302\u0323n"  # 6 chars, 4 codepoints
```

**Issue:** The two strings look identical but have different byte representations. Engines that do G2P on raw Unicode may treat them differently. Always normalize to NFC before any processing.

```python
def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFC', text)
```

**Specific Vietnamese issues:**
- `"đ"` (U+0111) vs `"d"` + combining mark — different char
- Tone mark position: `"ờ"` (ờ = ơ + huyền) vs alternative forms
- 8 tones × 6 vowel patterns = 45+ phonemes

**Reference:** [Nóm library](https://nom-vn.nrl.ai/tasks/text-normalization) — Vietnamese text processing

## Vietnamese-specific normalization (19-step pipeline)

Based on [VietNormalizer](https://arxiv.org/html/2603.04145) and similar work:

1. Unicode normalization (NFC)
2. Special character replacement (`&` → `và`, `@` → `a còng`)
3. URL/email removal
4. Punctuation normalization
5. Text cleaning (emojis, non-Latin)
6. Year range conversion (`2020-2025` → "from twenty twenty to twenty twenty-five")
7. Percentage conversion (`50%` → "fifty percent")
8. Date/time conversion
9. Ordinal conversion (`1st` → "first")
10. Thousand separator removal (`1,000` → "1000")
11. Currency conversion (`100,000 VND` → "one hundred thousand dong")
12. Phone number conversion (`0123456789` → "zero one two three...")
13. Decimal conversion (`3.14` → "three point one four")
14. Measurement unit conversion
15. Standalone number conversion
16. Lowercase normalization
17. Acronym replacement (CSV dictionary)
18. Non-Vietnamese word replacement (CSV dictionary)
19. Rule-based transliteration (algorithm → a-go-rít)

**Libraries:**
- [VietNormalizer](https://pypi.org/project/vietnormalizer/) — rule-based
- [PhoTextNormalization](https://huggingface.co/thivux/PhoTextNormalization) — neural
- [underthesea](https://github.com/undertheseanlp/underthesea) — Vietnamese NLP toolkit
- [PhoBERT](https://github.com/VinAIResearch/PhoBERT) — Vietnamese BERT

## Engine-specific G2P

| Engine | G2P method | Vietnamese? |
|---|---|---|
| piper-plus | espeak-ng (English-centric) | ❌ Custom G2P needed |
| Kokoro | Built-in phonemizer | ❌ |
| XTTS-v2 | Built-in | ❌ |
| F5-TTS | Character-based (no G2P) | ❌ |
| ChatTTS | Built-in (EN/ZH) | ❌ |
| MeloTTS-Vietnamese | Custom VI G2P, underthesea | ✅ |
| CosyVoice 2 | Built-in (CN-centric) | ❌ |

**Implication:** Mery's adapter layer may need to inject a G2P step before certain engines, or fall back to engines that handle the target language natively.

## Text length limits (per engine)

| Provider | Limit |
|---|---|
| OpenAI | 4096 characters |
| ElevenLabs | 5000 characters |
| Coqui | ~2000 chars (practical) |
| Piper | ~1000 chars (practical) |

**Mery needs:**
- Default limit: 4096 chars
- Configurable per-engine
- **Chunking strategy** for long text: split by sentence, synthesize each, concatenate audio
- Chunking must respect word boundary events (for karaoke-style UX)

## Multilingual mixed text

Vietnamese text often mixes English:
- "Tôi dùng VSCode" — "I use VSCode" (TTS should say "V-S-Code" not spell out V-S-C-O-D-E)
- "Hôm nay tôi học Machine Learning" — TTS may switch to English for ML terms
- Brand names, technical terms — typically keep as-is

**Mery needs:**
- Language detection per sentence/segment
- Language routing to engine that supports it
- Code-switching handling (skip or speak in dominant language)

## Tier classification

| Sub-item | Tier | Mery's priority |
|---|---|---|
| UTF-8 NFC normalization | Tier 1 BASE (correctness) | **P0** |
| Number/date/currency | Tier 1 BASE (UX) | P1 |
| Vietnamese pipeline | Tier 1 BASE (correctness for VI) | P1 |
| Engine-specific G2P | Tier 2 COMMON | P2 (only if engine doesn't support) |
| Long-text chunking | Tier 1 BASE (UX) | P1 |
| Multilingual mixed | Tier 3 PROVIDER-SPECIFIC | P3 (defer) |
| Lowercase normalization | Tier 2 COMMON | P2 |

## Reference projects

- [VietNormalizer](https://pypi.org/project/vietnormalizer/) — 19-step pipeline
- [underthesea](https://github.com/undertheseanlp/underthesea) — Vietnamese NLP
- [PhoTextNormalization](https://huggingface.co/thivux/PhoTextNormalization) — neural VI normalization
- [Nóm](https://nom-vn.nrl.ai/tasks/text-normalization) — diacritics
- [MeloTTS-Vietnamese](https://github.com/manhcuong02/MeloTTS_Vietnamese) — full VI pipeline
- [RULE-based G2P for Vietnamese](https://github.com/) — multiple research repos
- [Montreal Forced Aligner](https://mfa-models.readthedocs.io/en/latest/) — for VI alignment

## Decisions needed (future ADR)

1. **Mery's locale scope:** Vietnamese only, or multi-locale day-1?
2. **G2P strategy:** central layer in Mery, or per-engine adapter?
3. **Chunking strategy:** sentence-level (simple) or phoneme-level (precise)?
4. **Neural vs rule-based normalization:** neural (PhoTextNormalization) is better but slower
5. **Code-switching:** how to handle mixed VI/EN text?

**Recommendation for Mery MVP:** 
- NFC normalization always
- Number/date/currency via rule-based
- For Vietnamese, integrate VietNormalizer + underthesea
- Defer multi-locale and code-switching to Phase 2

## Cross-references

- `axes/01-engine-layer.md` — engine G2P support
- `axes/02-protocol.md` — text length limits
- `providers/08-melotts-vietnamese.md` — Vietnamese-specific engine
- `99-priority-matrix.md` — sequencing
