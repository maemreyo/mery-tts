# Provider 02 — Kokoro

**Last updated:** 2026-06-05
**Status in Mery:** Current (ADR-0004)

---

## Overview

Kokoro is a high-quality neural TTS model with 82M parameters, distributed under Apache 2.0. It's positioned as the "quality" engine in Mery's dual-engine strategy (piper-plus being "lightweight"). Active community ports include CoreML (Apple Neural Engine), CUDA, ROCm, WebGPU, and FastAPI.

## Specifications

| Attribute | Value |
|---|---|
| **License** | Apache 2.0 (commercial-safe) |
| **Languages** | 9 (EN/ZH/JA/ES/FR/IT/PT/HI/KO) |
| **Vietnamese** | ❌ |
| **Voice cloning** | Limited (no native zero-shot; small training data) |
| **Streaming** | ✅ (built-in streaming) |
| **Model size** | 82MB (fp32) → 160MB (fp16) → 92MB (int8) |
| **Latency P50** | ~100-300ms (CPU), 25x real-time on M4 ANE |
| **Hardware** | CPU, CoreML/ANE, CUDA, ROCm, WebGPU, DirectML |
| **Quantization** | fp32, fp16, int8 (palettized) |
| **Maintenance** | Active (7.3K GitHub stars) |
| **Adoption signals** | Mery's quality engine per ADR-0004 |

## Strengths

- **Apache 2.0** — commercially safe, patent grant
- **High quality** — most natural English listening among local engines
- **Multi-platform** — CoreML, CUDA, ROCm, WebGPU, DirectML all supported
- **Active community** — multiple ports maintained
- **Streaming** — built-in chunked output
- **Voice blending** — `af_bella(2)+af_heart(1)` syntax for multi-voice

## Weaknesses

- **English-centric** — 8 of 9 languages are non-English, Vietnamese not included
- **No real voice cloning** — limited speaker adaptation
- **Slower than piper-plus** on CPU (100-300ms vs 38ms)
- **Quantization quality** — int4 has noticeable quality loss

## Mery integration notes

ADR-0004 chose Kokoro as Mery's quality engine. Key integration points:
- Package: `kokoro-onnx>=0.4` (optional dependency, CPU ONNX backend, no PyTorch/CUDA)
- Python API: `kokoro_onnx` direct (no subprocess per Grill Q1)
- Entry point: `mery_tts.engines` group → `mery_tts.engines.kokoro.adapter:KokoroAdapter`
- Engine note: "broken Kokoro install must not break Piper-plus" (optional deps in pyproject)

## Performance variants

| Variant | Platform | Latency | Reference |
|---|---|---|---|
| CPU (kokoro-onnx) | Universal | 100-300ms | Default |
| CoreML/ANE (kokoro-coreml) | Apple Silicon | 25x real-time M4 | laishere/kokoro-coreml |
| CUDA | NVIDIA GPU | Best perf | kokoro-onnx with CUDA EP |
| ROCm | AMD GPU | Experimental | kokoro-fastapi-rocm |
| WebGPU | Browser | In-browser inference | TLD2 docs |
| FastAPI | Server | With streaming | remsky/Kokoro-FastAPI |

## Voice cloning in Kokoro

- **Type:** Limited / partial
- **Reference:** Not zero-shot; some research on speaker adaptation
- **Output:** Quality varies significantly from training data
- **Vietnamese voice cloning:** Not natively supported

## Reference

- [hexgrad/kokoro](https://github.com/hexgrad/kokoro) — main repo
- [laishere/kokoro-coreml](https://github.com/laishere/kokoro-coreml) — CoreML/ANE port
- [remsky/Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) — FastAPI server with streaming
- [kokoro TLD2 docs](https://tld2.io/docs/tts-implementation.html) — WebGPU + browser

## Engine × tier classification

| Sub-item | Kokoro |
|---|---|
| Synthesize | Tier 1 BASE ✅ |
| Voice selection | Tier 1 BASE ✅ |
| Output format | Tier 1 BASE ✅ |
| Speed control | Tier 1 BASE ✅ |
| Streaming | Tier 2 COMMON ✅ |
| Word timing | Tier 2 COMMON ✅ (via Kokoro-FastAPI) |
| Voice cloning | Tier 3 (limited) |
| SSML | Tier 3 (preprocessed) |
| Multilingual | 9 langs |
| Vietnamese | ❌ |

## Decision status

✅ Active in Mery (ADR-0004). No migration needed.

## Apple Silicon optimization (P2)

When Mery is ready to scale Engine axis 1.1 (CoreML adapter), Kokoro is the primary target. The `laishere/kokoro-coreml` reference shows the pattern: split model into ANE-friendly stages (no RangeDim, fixed shapes), separate fp16 ANE from fp32 DSP stages, int8 palettized for size.
