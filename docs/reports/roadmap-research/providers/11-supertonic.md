# Provider 11 — Supertonic

**Last updated:** 2026-06-05
**Status in Mery:** Future candidate (on-device + multilingual)

---

## Overview

Supertonic is a lightning-fast, on-device multilingual TTS system from Supertone Inc. The latest **Supertonic 3** (April–May 2026) is a 99M-parameter model trained on a ConvNeXt + speech autoencoder + flow-matching architecture, supporting 31 languages with no separate language adapters. Runs entirely locally via ONNX Runtime, optimized for ultra-low latency on consumer hardware (167× real-time on M4 Pro).

## Specifications

| Attribute | Value |
|---|---|
| **License** | MIT (commercial-safe) |
| **Languages** | 31 (no language tag needed; pass `lang="na"` for language-agnostic) |
| **Vietnamese** | ✅ (one of 31 supported) |
| **Voice cloning** | ✅ via Voice Builder (browser-based, separate from CLI inference) |
| **Streaming** | ✅ (built into ONNX inference) |
| **Model size** | 99M params (Supertonic 3); older Supertonic 2 line is 66M |
| **Latency P50** | Sub-100ms TTFA; 167× real-time on M4 Pro, 1000+ chars/sec on M1 |
| **Hardware** | CPU (ONNX), WebGPU/WASM (browser), no GPU required |
| **Sample rate** | 44.1kHz 16-bit WAV (native, no upsampler needed) |
| **Quantization** | fp32 / fp16 via ONNX Runtime |
| **Maintenance** | Active (Supertone Inc. team, regular updates) |
| **Multi-runtime SDKs** | Python, Node.js, Browser (WebGPU), Java, C++, C#, Go, Swift, iOS, Rust, Flutter |

## Strengths

- **MIT licensed** — fully commercial-safe, no patent concerns
- **99M params** — among smallest SOTA-quality models; instant cold starts
- **31 languages** without explicit language tags — easiest multilingual onboarding in 2026
- **Raw text input** — handles numbers, dates, currency, abbreviations without preprocessing
- **10 inline expression tags** (`<laugh>`, `<breath>`, `<sigh>`, etc.) — natural prosody without reference audio
- **Multi-runtime SDKs** — same ONNX model usable from browser, mobile, server, edge
- **44.1kHz native output** — studio-grade quality without external upsampling
- **Apple Silicon friendly** — fastest path for Mery's P2 CoreML/ANE strategy

## Weaknesses

- **Voice cloning via separate web tool** — Voice Builder is browser-based, not part of core SDK; programmatic cloning flow not documented as of June 2026
- **Newest in the field** (April–May 2026) — production stability track record still building
- **Smaller model = lower ceiling** on emotional expressiveness vs. 1B+ class models
- **Browser inference requires WebGPU** — no fallback for older devices

## Mery integration notes

Positioned as the **on-device Tier 1 engine** alongside piper-plus and Kokoro. Differentiation:
- **vs. piper-plus (MIT, 38ms CPU)**: Supertonic is 167× RT on M4 Pro (vs. piper-plus's 50–100×), but piper-plus is more battle-tested
- **vs. Kokoro (Apache 2.0, 9 langs)**: Supertonic has 31 langs (3.4× more) and Vietnamese native support
- **vs. MeloTTS-Vietnamese (MIT, Vietnamese-only)**: Supertonic trades narrow Vietnamese quality for broad multilingual coverage

Best fit for Mery if we want a **single lightweight engine that covers Vietnamese + 30 other languages** without separate G2P pipelines.

## Performance variants

| Variant | Platform | Latency | Reference |
|---|---|---|---|
| Browser (WebGPU) | Chromium/Safari | Sub-100ms | supertonic-tts.com |
| Python (ONNX) | Desktop/server | ~150ms TTFA | `py/example_onnx.py` |
| Node.js | Server | Streaming | `nodejs/` example |
| Swift / iOS | Apple | Native | `swift/` + `ios/` |
| Rust | Edge / server | Memory-safe | `rust/` |
| C++ | Embedded | Highest perf | `cpp/` |

## Reference

- [supertone-inc/supertonic](https://github.com/supertone-inc/supertonic) — main repo (Supertonic 3)
- [Supertone/supertonic-3](https://huggingface.co/Supertone/supertonic-3) — HF model weights
- [supertonic-tts.com](https://supertonic-tts.com/) — official site
- [supertonic3.github.io](https://supertonic3.github.io/) — Supertonic 3 demo
- [Voice Builder demo](https://supertonic.supertone.ai/voice-builder) — voice cloning UI
- [supertone-inc/supertonic-py](https://github.com/supertone-inc/supertonic-py) — Python PyPI package

## Engine × tier classification

| Sub-item | Supertonic |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ (preset voices) |
| Output format | Tier 1 BASE ✅ (44.1kHz WAV native) |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 3 (not in core API) |
| Voice cloning | Tier 3 (via Voice Builder only) |
| SSML | Tier 3 (inline tags only, not full SSML) |
| Multilingual | 31 langs |
| Vietnamese | ✅ Native |
| Expression tags | 10 inline tags |
| Apple Silicon | Optimized |

## Decision status

🟡 **Future candidate** for Mery's lightweight multilingual engine. Awaiting:
- Voice cloning in core SDK (currently web-only via Voice Builder)
- Production stability track record beyond 6 months
- Decision on Vietnamese strategy (Supertonic covers it natively, but MeloTTS-Vietnamese has finer dialect quality)

## Strategic fit

If Mery wants to expand beyond English-quality (Kokoro) and Vietnamese-specific (MeloTTS-VI) with a single on-device engine that covers 31 languages, **Supertonic is the most attractive 2026 option** — it competes with Kokoro on speed and with MeloTTS-VI on Vietnamese coverage, while adding 28 more languages.
