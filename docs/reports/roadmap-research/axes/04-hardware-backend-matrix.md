# Axis 04 — Hardware Backend Matrix (HIDDEN)

**Last updated:** 2026-06-05
**Status in roadmap:** **Not listed** — discovered via research
**Why it matters:** Engine × Hardware × EP = N×M matrix. CoreML is one slice. Real story involves ONNX EPs, ANE, CUDA, ROCm, WebGPU, quantization.

---

## What this axis covers

How Mery selects the right hardware backend for a given engine on a given machine. Today, ADR-0004 says "Python API + ONNX Runtime" but doesn't say which Execution Provider (EP) to use or how to handle the case where the user's machine has multiple accelerators.

## The matrix

| Backend | Platform | Engines that support | Performance | Notes |
|---|---|---|---|---|
| **CPU** (no EP) | All | All | Baseline | Fallback for everything |
| **CoreML EP** | macOS / iOS | ONNX engines (Kokoro) | 25x real-time M4, 17x iPhone 16 Pro | ANE + GPU |
| **CUDA EP** | NVIDIA GPU | All ONNX engines | Best perf | Dev-friendly, common |
| **ROCm EP** | AMD GPU | All ONNX engines | Experimental | kokoro-fastapi-rocm is reference |
| **DirectML EP** | Windows | All ONNX engines | General | Cross-vendor |
| **WebGPU** | Browser | TTS in browser (Kokoro WebGPU ref) | In-browser inference | No server needed |
| **ANE (direct)** | Apple Silicon | Specific engines (Kokoro refactored) | Best perf on M-series | Needs ANE-friendly graph |

## Engine × Backend matrix (Mery's catalog)

| Engine | CPU | CoreML | CUDA | ROCm | DirectML | WebGPU | ANE |
|---|---|---|---|---|---|---|---|
| piper-plus | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Kokoro | ✅ | ✅ (laishere/kokoro-coreml) | ✅ | ✅ (kokoro-fastapi-rocm) | ✅ | ✅ (Kokoro WebGPU) | ✅ |
| XTTS-v2 | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| F5-TTS | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| OpenVoice v2 | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Fish Audio S2 | ✅ | ❌ | ✅ (SGLang) | ❌ | ✅ | ❌ | ❌ |
| CosyVoice 2 | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| RVC | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| MeloTTS-VI | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |

## Quantization

| Format | Size reduction | Quality loss | When to use |
|---|---|---|---|
| **fp32** | 1.0x (baseline) | None | Rare (default in PyTorch) |
| **fp16** | 0.5x | None | ANE-friendly, GPU standard |
| **int8 (palettized)** | 0.25x | Minimal | M4/ANE best practice |
| **int4** | 0.125x | Noticeable (some engines) | Avoid for TTS |

**Recommendation for Mery:**
- Default: **fp16** for GPU/CUDA/CoreML EPs
- Fallback: **fp32** for CPU
- **int8** for ANE-specific paths (M-series optimization)
- Avoid int4 for TTS (quality loss too high for natural speech)

## Reference projects

- [laishere/kokoro-coreml](https://github.com/laishere/kokoro-coreml) — Kokoro with CoreML/ANE, 25x M4
- [remsky/Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) — ROCm + CUDA + CPU
- [onnxruntime execution providers](https://onnxruntime.ai/docs/execution-providers/) — full EP matrix
- [TLD2 Kokoro WebGPU](https://tld2.io/docs/tts-implementation.html) — browser inference
- [BentoML TTS guide](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models) — production deployment patterns

## Hidden risks

1. **N×M test matrix**: 8 engines × 7 backends = 56 combinations. Need CI to cover.
2. **Apple Silicon only** for ANE — Intel Mac users get nothing
3. **Backend drift**: ONNX Runtime releases new EPs; pin to known-good versions
4. **Bundle size**: shipping multiple EPs in pyproject optional-deps balloons install size
5. **EP selection on user machine**: what if user has both CUDA and CoreML (e.g., eGPU on Mac)? Need policy.

## Decisions needed (future ADR)

- **EP selection policy**: explicit (user chooses), implicit (auto-detect best), or config file?
- **Optional dependencies**: separate pyproject extras per backend (`[core]`, `[cuda]`, `[coreml]`)?
- **CI matrix**: which backends to test in CI vs deferred to user?
- **WebGPU in browser**: separate Mery product (browser-only, no server)?

## Tier classification

| Sub-item | Tier | Mery's priority |
|---|---|---|
| CPU baseline | Tier 1 BASE | **P0** (always works) |
| CoreML/ANE | Tier 2 COMMON (Apple) | P2 |
| CUDA | Tier 2 COMMON (NVIDIA) | P2 (dev-friendly) |
| ROCm | Tier 3 PROVIDER-SPECIFIC (AMD) | P3 (experimental) |
| DirectML | Tier 3 PROVIDER-SPECIFIC (Windows) | P3 |
| WebGPU (browser) | Tier 3 PROVIDER-SPECIFIC | P3 (separate product?) |
| Quantization (fp16) | Tier 2 COMMON | P1 (default) |
| Quantization (int8) | Tier 3 PROVIDER-SPECIFIC | P2 (ANE) |

## Cross-references

- `axes/01-engine-layer.md` — engine-level capabilities
- `axes/06-operations-and-observability.md` — backend health monitoring
- `providers/` — per-engine backend support
- `99-priority-matrix.md` — sequencing
