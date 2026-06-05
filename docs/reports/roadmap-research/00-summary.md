# 00 — Summary

**Last updated:** 2026-06-05

---

## TL;DR

There is a **Tier 1 BASE set of 7 features** that every TTS provider in 2026 exposes (synthesize, voice selection, output format, speed, language, errors, health). Mery's current `/v1` contract covers 6/7 — **language selection is a gap**. Around BASE sits Tier 2 COMMON (9 features, most providers) and Tier 3 PROVIDER-SPECIFIC (10+ differentiators). The 3-axis roadmap in the diagram covers ~70% of scale directions. Research uncovered 4 hidden axes (hardware matrix, governance, operations, locale) that the diagram doesn't list.

## The 7 BASE features (table-stakes 2026)

| # | Feature | Mery covers? |
|---|---|---|
| 1 | Synthesize (text → audio) | ✅ ADR-0005 |
| 2 | Voice selection | ✅ ADR-0005 |
| 3 | Output format (codec, sample rate, bit depth, channels) | ✅ ADR-0005 |
| 4 | Speed control (0.25x → 4.0x) | ✅ ADR-0005 |
| 5 | **Language selection** | ❌ **GAP** |
| 6 | Error response schema | ✅ ADR-0010 |
| 7 | Health/ready endpoint | ✅ ADR-0005 |

## Key insight: BASE exists, roadmap covers it

The user's question — "có những thứ base chứ nhỉ?" (there are BASE things, right?) — is **yes, definitively**. Mery's design instinct (engine adapter ABC, /v1 contract, EngineRegistry) already aligns with the BASE tier. The gap is small (language field), the architecture is sound.

## The 4 hidden axes (research uncovered, diagram didn't list)

1. **Hardware backend matrix** — CoreML/ANE is one slice. Real story: ONNX Runtime has CoreML/CUDA/ROCm/DirectML EPs; ANE gives 25x real-time on M4; WebGPU exists for browser; quantization (int8/int4/fp16) trades size for quality. Each engine × each hardware = N×M test matrix. **Needs ADR for backend selection policy.**

2. **Governance & licensing** — Voice cloning without governance = legal/PR disaster. EU AI Act (effective Aug 2026) requires synthetic audio disclosure. Texas/Tennessee have state laws. SPDX 3.0 AI Profile for license tracking. AudioSeal watermarking. CAP spec for provenance. **Needs ADR before opening community catalog.**

3. **Operations & observability** — Production TTS needs: health/ready/live (3 distinct), metrics (P50/P95/P99), GPU management, model warmup, batching, concurrency, timeout/cancellation, graceful shutdown, backpressure. 9 documented failure modes. **Not glamorous but production-critical.**

4. **Locale & text normalization** — Especially Vietnamese: UTF-8 NFC vs NFD, VietNormalizer 19-step pipeline, engine-specific G2P. **This is BASE correctness, not a feature** — if Mery reads "tiền" (money) as "ti-ên" (fairy), it's broken regardless of how good the engine is.

## Strategic horizon validation

The diagram's "OpenAI compat · community catalog → Ollama for TTS" framing is **correct**. Replicating Ollama's OCI registry pattern (SHA256 content-addressable blobs, 7 layer types, manifest+blobs, parallel chunked downloads) is the right architectural choice. The "just works" UX is the moat.

## Engine landscape summary (12 engines)

| Tier | Engines |
|---|---|
| **MIT/Apache (commercial-safe)** | piper-plus, kokoro, MeloTTS, OpenVoice v2, CosyVoice 2, RVC |
| **Mixed license (research use OK)** | Fish Audio S2 (Research), F5-TTS (CC-BY-NC weights), ChatTTS (AGPL/CC-BY-NC) |
| **License ambiguous post-Coqui** | XTTS-v2 (CPML) |
| **Vietnamese-native** | MeloTTS-Vietnamese (fine-tune, MIT), Fish Audio S2 (Research, 80+ langs) |

**Most engines do NOT support Vietnamese natively.** This is a real gap for Mery's creator (Vietnamese teacher who builds Zam Reader).

## Provider-specific features to NOT build (yet)

Emotion vectors (ElevenLabs), style prompts (OpenAI gpt-4o-mini-tts), voice design from text, latency optimization tiers, singing synthesis, voice conversion, cross-lingual cloning, watermarking, realtime full-duplex API, speaker diarization input.

**Reason**: each of these is its own product line. Build extension points (custom fields, separate endpoints) so future wrap is possible without polluting core contract.

## Open questions (need user input)

1. **Vietnamese strategy**: chờ upstream engines, hay tự fine-tune MeloTTS-Vietnamese?
2. **OpenAI compat path**: `/openai/v1/` separate, hay `/v1/` với header?
3. **Voice cloning governance**: community-uploaded cloned voices có được phép không?
4. **Hardware backend priority**: Apple Silicon trước, NVIDIA trước, hay song song?
5. **Locale scope**: chỉ Vietnamese, hay multi-locale ngay từ đầu?

## File map

- `axes/01-03` — 3 explicit roadmap axes
- `axes/04-07` — 4 hidden axes
- `providers/01-10` — 10 engine/provider inventory files
- `99-priority-matrix.md` — P0/P1/P2/P3 ordering

See `README.md` for full index.
