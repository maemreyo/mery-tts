# Roadmap Research — Scale Direction Knowledge Dump

**Date:** 2026-06-05
**Source:** Web research synthesis (5 parallel librarian agents + 1 codebase grounding)
**Purpose:** Reference material for future ADRs covering Mery's 3-axis scale roadmap + 4 hidden axes.

---

## What this directory is

A knowledge dump. Each file is **reference material** for a future ADR or design decision, not a design document itself. When Mery needs to decide on (e.g.) voice cloning governance, the relevant file under `axes/05-governance-and-licensing.md` collects the research, citations, and tradeoffs in one place.

## What this directory is NOT

- Not new ADRs (those live in `docs/adr/`)
- Not engine-specific implementation (that's runtime code)
- Not decisions (decisions belong in ADRs that cite this research)

## File index

### 00 — Overview

| File | Purpose |
|---|---|
| `00-summary.md` | TL;DR, key findings, the 4 hidden axes, condensed priority matrix |
| `99-priority-matrix.md` | Consolidated P0/P1/P2/P3 view across all axes + providers |

### axes/ — Scale direction deep-dives

| File | Sub-items | Status |
|---|---|---|
| `axes/01-engine-layer.md` | CoreML adapter, Word timing, Voice cloning | Explicit in roadmap |
| `axes/02-protocol.md` | TTFB streaming, SSML markup, OpenAI compat | Explicit in roadmap |
| `axes/03-ecosystem.md` | Client SDKs, Model registry, Native bridge | Explicit in roadmap |
| `axes/04-hardware-backend-matrix.md` | ONNX EPs, CoreML/ANE, CUDA/ROCm, WebGPU, quantization | **Hidden axis** |
| `axes/05-governance-and-licensing.md` | SPDX tracking, voice cloning consent, deepfake, EU AI Act | **Hidden axis** |
| `axes/06-operations-and-observability.md` | Health/ready/live, metrics, batching, concurrency, backpressure | **Hidden axis** |
| `axes/07-locale-and-text-normalization.md` | UTF-8 NFC, Vietnamese pipeline, engine-specific G2P | **Hidden axis** |

### providers/ — TTS engine / API inventory

| File | License | Vietnamese | Voice cloning | Streaming | Tier |
|---|---|---|---|---|---|
| `providers/01-piper-plus.md` | MIT | ❌ Custom G2P needed | ✅ Speaker embedding | ✅ | Current (ADR-0004) |
| `providers/02-kokoro.md` | Apache 2.0 | ❌ | Limited | ✅ | Current (ADR-0004) |
| `providers/03-xtts-v2.md` | CPML (ambiguous) | ❌ | ✅ 6s ref | ✅ | Future candidate |
| `providers/04-f5-tts.md` | MIT (code) / CC-BY-NC-4.0 (weights) | ❌ Community ports | ✅ 5-15s ref | ✅ | Future candidate |
| `providers/05-openvoice-v2.md` | MIT | ❌ | ✅ 1-5s ref + cross-lingual | ✅ | Voice cloning base |
| `providers/06-fish-audio-s2.md` | Research License | ✅ Native | ✅ 10-30s ref | ✅ SGLang ~100ms TTFA | **Multilingual expansion** |
| `providers/07-cosyvoice-2.md` | Apache 2.0 | ❌ | ✅ 3s zero-shot | ✅ 150ms TTFA | Future candidate |
| `providers/08-melotts-vietnamese.md` | MIT | ✅ Native (fine-tune) | ❌ | ✅ | **Vietnamese path** |
| `providers/09-chattts.md` | AGPL-3.0 (code) / CC-BY-NC-4.0 (weights) | ❌ | ❌ | ✅ | Reference (license issues) |
| `providers/10-rvc.md` | MIT | Any (via pipeline) | ✅ Fine-tune, 10min data | ✅ Real-time | Voice conversion |
| `providers/11-supertonic.md` | MIT | ✅ Native (31 langs) | ✅ Voice Builder | ✅ 167× RT on M4 Pro | **On-device multilingual** |
| `providers/12-omnivoice.md` | Apache 2.0 | ✅ Native (600+ langs) | ✅ Zero-shot 3-25s | ❌ | **Universal language coverage** |
| `providers/13-chatterbox.md` | MIT | ❌ English | ✅ 5-10s + emotion | ✅ Turbo sub-200ms | English voice cloning leader |
| `providers/14-orpheus.md` | Apache 2.0 | ❌ (EN + 8 research) | ✅ Zero-shot | ✅ 100-200ms | LLM-ecosystem TTS |
| `providers/15-dia.md` | Apache 2.0 | ❌ English | ❌ (preset only) | ✅ | Multi-speaker dialogue |
| `providers/16-higgs-audio-v2.md` | Apache 2.0 | ❌ English | ✅ Built-in | ✅ | SOTA quality ceiling (5.77B) |
| `providers/17-qwen3-tts.md` | Apache 2.0 | ❌ (10 langs, no VI) | ✅ 3s + design | ✅ 97ms first token | Multilingual + cloning champion |
| `providers/18-neutts-air.md` | Apache 2.0 | ❌ English | ✅ 3-15s | ✅ Real-time CPU | On-device English + watermark |
| `providers/19-voxcpm2.md` | Apache 2.0 | ✅ Native (30 langs) | ✅ 2 modes + design | ✅ RTF 0.13-0.30 | Studio 48kHz multilingual |

## Tier convention

Each file tags features using the cross-provider tier convention:

- **Tier 1 — BASE**: Every TTS provider has it. Table-stakes in 2026.
- **Tier 2 — COMMON**: Most providers have, not universal.
- **Tier 3 — PROVIDER-SPECIFIC**: Few providers, premium/optional.

## How to use these files

1. **Writing a new ADR**? Read the relevant `axes/NN-*.md` first — it collects research, options, citations, and known risks.
2. **Adding a new engine**? Read `providers/` to find candidates + license posture.
3. **Validating a scale decision**? Check `99-priority-matrix.md` for ordering rationale.
4. **Closing a gap**? Search for `[GAP]` tags — these mark research needs that the repo hasn't filled yet.

## Research sources (June 2026)

- 5 parallel librarian agents on engine landscape, protocol standards, voice registries, client SDKs, base patterns
- 1 explore agent on Mery's current state (12 ADRs, architecture, design decisions)
- OpenAI, ElevenLabs, Azure, Google, LiveKit, Soniox official docs
- GitHub: piper-plus, kokoro, kokoro-coreml, Kokoro-FastAPI, XTTS, F5-TTS, OpenVoice, Fish Speech, RVC, MeloTTS-Vietnamese
- Ollama, HuggingFace, CivitAI registry architecture
- RealtimeTTS, LiveKit Agents abstraction patterns
- EU AI Act, SPDX 3.0 AI Profile, CAP specification, C2PA
- Bitwarden / 1Password browser-extension architecture
- Orval, openapi-typescript, hey-api SDK generation
- AudioSeal / Perth watermarking, VietNormalizer, Nóm Vietnamese NLP
- **2025-2026 OSS TTS additions:** Supertonic (Supertone Inc.), OmniVoice (k2-fsa/Xiaomi), Chatterbox (Resemble AI), Orpheus (Canopy Labs), Dia (Nari Labs), Higgs Audio V2 (Boson AI), Qwen3-TTS (Alibaba), NeuTTS Air (Neuphonic), VoxCPM2 (OpenBMB)

## Updating this directory

When new research surfaces, **append** a dated section at the bottom of the relevant file. Do not rewrite prior sections. Each file has a "Last updated" header.
