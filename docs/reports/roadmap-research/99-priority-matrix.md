# 99 — Priority Matrix

**Last updated:** 2026-06-05
**Purpose:** Consolidated P0/P1/P2/P3 view across all axes + providers.

---

## P0 (months 1-2, parallel) — Strategic unlock

| Item | Axis | Tier | Effort | Value | Risk |
|---|---|---|---|---|---|
| **Language selection field in /v1 contract** | Protocol | Tier 1 BASE | XS | Closes BASE gap | None |
| **OpenAI /v1/audio/speech compat** | Protocol | Tier 1 BASE (distribution) | M | **High — distribution hack** | Auth/schema mapping |
| **Model registry MVP (synthetic voices only)** | Ecosystem | Tier 1 BASE | L | High — flywheel | Bandwidth, governance |
| **Governance ADR (consent, license, takedown)** | Hidden (governance) | Tier 1 BASE (legal) | M | **Critical for catalog** | None (defer cloned voices) |
| **Ed25519 manifest signing** | Hidden (governance) | Tier 2 COMMON | S | Manifest integrity | Key management |

## P1 (months 3-4, parallel) — Depth

| Item | Axis | Tier | Effort | Value | Risk |
|---|---|---|---|---|---|
| **TTFB streaming (≤300ms P50)** | Protocol | Tier 1 BASE (realtime) | M | LLM-voice unlock | Engine batch-only |
| **Word timing (per-word/phoneme events)** | Engine | Tier 2 COMMON | L | Zam Reader UX | Drift, accuracy |
| **Hardware backend selection policy ADR** | Hidden (hardware) | Tier 1 BASE (prod) | S | Clarity for implementers | None |
| **fp16 quantization as default** | Hidden (hardware) | Tier 2 COMMON | S | GPU perf | Minimal quality loss |
| **UTC NF C + base text normalization** | Hidden (locale) | Tier 1 BASE (correctness) | S | Vietnamese correctness | None |
| **VietNormalizer + underthesea integration** | Hidden (locale) | Tier 1 BASE (VI) | M | Vietnamese pipeline | None |
| **Health/ready/live endpoints (3 distinct)** | Hidden (ops) | Tier 1 BASE | S | Production deploy | None |
| **Prometheus metrics** | Hidden (ops) | Tier 1 BASE | M | Observability | None |
| **Concurrency + rate limits** | Hidden (ops) | Tier 1 BASE | S | Stability | None |
| **Per-request timeout + client cancellation** | Hidden (ops) | Tier 1 BASE | M | UX | Engine cancel support |
| **Failure mode contract tests (9 modes)** | Hidden (ops) | Tier 1 BASE | M | Correctness | None |
| **Long-text chunking (sentence-level)** | Hidden (locale) | Tier 1 BASE | S | UX | Concatenation quality |

## P2 (months 5-6) — Performance & DX

| Item | Axis | Tier | Effort | Value | Risk |
|---|---|---|---|---|---|
| **CoreML adapter (Kokoro on ANE)** | Engine + Hardware | Tier 2 COMMON | L | Apple users 25x speed | Engine refactor |
| **Client SDKs (TS first, Orval-generated)** | Ecosystem | Tier 2 COMMON | M | Zam Reader + adoption | Version drift |
| **CUDA EP** | Hardware | Tier 2 COMMON | S | Dev-friendly | None |
| **int8 quantization (palettized for ANE)** | Hardware | Tier 3 | S | M-series optimization | Quality loss |
| **DirectML EP (Windows)** | Hardware | Tier 3 | S | Windows users | None |
| **AudioSeal watermarking** | Hidden (governance) | Tier 3 | M | Provenance | None |
| **Deepfake detection at upload** | Hidden (governance) | Tier 2 | L | Required for cloned voices | False positives |
| **G2P layer for engines that need it** | Hidden (locale) | Tier 2 | M | Multi-locale | None |
| **Dynamic batching (opt-in)** | Hidden (ops) | Tier 3 | M | Throughput | Latency trade-off |
| **Streaming backpressure** | Hidden (ops) | Tier 2 | M | Slow-client handling | None |
| **Graceful shutdown protocol** | Hidden (ops) | Tier 2 | S | Ops | None |
| **SDK generation CI** | Ecosystem | Tier 2 | S | Drift prevention | None |

## P3 (months 7+, gated by prerequisites) — Defer

| Item | Axis | Tier | Effort | Value | Risk | Gate |
|---|---|---|---|---|---|---|
| **Voice cloning (engine support)** | Engine | Tier 3 | L | ElevenLabs killer | **Deepfake legal** | Governance ADR + moderation pipeline |
| **Cloned voices in community catalog** | Ecosystem | Tier 3 | L | Personal voices | **PR disaster** | Voice cloning policy + consent flow |
| **SSML preprocessing** | Protocol | Tier 3 (local) | L | Standard compat | Engine feature fragmentation | User demand |
| **Native Messaging transport** | Ecosystem | Tier 3 | L | No open port | OS-level debug friction | Chrome/Firefox store policy |
| **MeloTTS-Vietnamese fine-tune** | Engine | Tier 1 (for VI) | XL | Native VI | Training infra, maintenance | Upstream engines don't add VI |
| **Fish Audio S2 integration** | Engine | Tier 2 | L | 80+ langs including VI | Research License terms | Multi-locale scope decision |
| **C2PA provenance** | Hidden (governance) | Tier 3 | L | Standard compliance | None | AudioSeal first |
| **WebGPU (browser-only Mery)** | Hidden (hardware) | Tier 3 | XL | Browser inference | Separate product | Product decision |
| **Real-time WebSocket full-duplex API** | Protocol | Tier 3 | XL | Realtime agents | Massive engineering | User demand for voice agents |
| **Cross-lingual cloning** | Engine | Tier 3 | XL | Magic feature | All voice cloning risks | Voice cloning first |
| **Singing voice synthesis** | Engine | Tier 3 | XL | New domain | Different models entirely | Out of scope decision |
| **Emotion vectors / style prompts** | Protocol | Tier 3 | M | ElevenLabs parity | Engine-specific | Engine support |
| **Multilingual code-switching** | Hidden (locale) | Tier 3 | L | Mixed VI/EN UX | None | Multi-locale scope |

## Engine acquisition priority

| Phase | Engine | Why | License |
|---|---|---|---|
| **Current (ADR-0004)** | piper-plus, kokoro | Lightweight + quality dual-engine, MIT/Apache | ✅ |
| **Phase 2 (months 5-6)** | Fish Audio S2 (if Research License OK) | 80+ langs including Vietnamese | ⚠️ |
| **Phase 2 (months 5-6)** | OpenVoice v2 | Voice cloning base, cross-lingual, MIT | ✅ |
| **Phase 2 (months 5-6)** | MeloTTS-Vietnamese | Vietnamese-native, MIT (fine-tune) | ✅ |
| **Phase 3 (months 7+)** | F5-TTS | Quality cloning, MIT (code) / CC-BY-NC (weights) | ⚠️ |
| **Phase 3 (months 7+)** | CosyVoice 2 | Quality zero-shot, Apache 2.0 | ✅ |
| **Defer** | XTTS-v2 | License ambiguous (post-Coqui) | ⚠️ |
| **Defer** | ChatTTS | AGPL/CC-BY-NC — viral + non-commercial | ❌ |
| **Defer** | RVC | Voice conversion, not core TTS | ✅ for that purpose |
| **Phase 2 candidate** | Supertonic (Supertone Inc., MIT, 99M) | On-device multilingual (31 langs incl. VI), 167× RT M4 Pro | ✅ |
| **Phase 2 candidate** | VoxCPM2 (OpenBMB, Apache 2.0, 2B) | Vietnamese + 29 langs, 48kHz, voice design | ✅ |
| **Phase 2 candidate** | Qwen3-TTS (Alibaba, Apache 2.0, 0.6-1.7B) | 10 langs, 97ms first token, 3s cloning, OpenAI compat | ✅ |
| **Phase 2 candidate** | NeuTTS Air (Neuphonic, Apache 2.0, 748M) | On-device English, 3s cloning, Perth watermark (EU AI Act) | ✅ |
| **Phase 3 candidate** | Chatterbox (Resemble AI, MIT, 350M) | English cloning, 63.75% vs ElevenLabs, sub-200ms Turbo | ✅ |
| **Phase 3 candidate** | Orpheus (Canopy Labs, Apache 2.0, 3B/1B/400M/150M) | LLM-ecosystem TTS, vLLM-compatible, 4 model sizes | ✅ |
| **Phase 3 candidate** | Higgs Audio V2 (Boson AI, Apache 2.0, 5.77B) | Quality ceiling, SOTA on TTS Arena, needs 24GB+ VRAM | ✅ |
| **Phase 3 candidate** | Dia 1.6B (Nari Labs, Apache 2.0) | Multi-speaker dialogue, non-verbal tags | ✅ |
| **Strategic watchlist** | OmniVoice (k2-fsa, Apache 2.0) | 600+ langs, 40× RTF, GPU-only — universal fallback | ✅ |

## Tier ↔ priority translation

| Tier | Mery default priority |
|---|---|
| Tier 1 BASE (correctness, contract) | **P0** (build first, non-negotiable) |
| Tier 1 BASE (distribution, governance) | **P0** (strategic unlock) |
| Tier 2 COMMON (most providers) | **P1** (build before broad adoption) |
| Tier 2 COMMON (optional, engine-specific) | **P2** (when demand exists) |
| Tier 3 PROVIDER-SPECIFIC | **P3** (defer; document as extension point) |

## Sequencing rationale

The P0 items are the **"Ollama for TTS" strategic unlock**. OpenAI compat + Model registry (synthetic-only) + governance ADR are the 3 legs of the stool. Without any one, the strategic horizon fails.

The P1 items are the **depth moves** that turn Mery from "viable" to "production-grade for LLM-voice + Vietnamese" — the two strongest use cases (Zam Reader first consumer, LLM voice assistants being the "killer app" per README §37).

The P2 items are **performance + DX** — important for adoption, not for existence.

The P3 items are **gated by prerequisites** — voice cloning waits for governance, multi-locale waits for scope decision, Native Messaging waits for policy forcing.

## 2025-2026 engine landscape — strategic shifts

The June 2026 dump added 9 engines (supertonic, omnivoice, chatterbox, orpheus, dia, higgs-audio-v2, qwen3-tts, neutts-air, voxcpm2). Three strategic shifts affect the priority matrix above:

1. **Vietnamese no longer requires MeloTTS-VI fine-tune.** Supertonic (31 langs incl. VI, on-device) and VoxCPM2 (30 langs incl. VI, studio 48kHz) both cover Vietnamese natively in Apache 2.0/MIT. The Phase 2 path of "MeloTTS-Vietnamese fine-tune" can be deprioritized unless per-dialect quality matters.

2. **Voice cloning governance can de-risk faster.** NeuTTS Air's built-in Perth watermarking satisfies EU AI Act Art. 50 traceability out of the box. Combined with Chatterbox-Turbo's MIT license (vs. XTTS-v2's CPML), the Voice cloning P3 gate (governance ADR) becomes more attractive to lift to P2.

3. **Multilingual "Ollama for TTS" is now achievable.** Qwen3-TTS (10 langs) + Supertonic (31 langs) + VoxCPM2 (30 langs) collectively cover 31+ languages with voice cloning, sub-200ms latency, and Apache 2.0/MIT licenses. The "scale to N languages" axis is no longer research-blocked.

## Effort legend

- **XS:** < 1 day
- **S:** 1-3 days
- **M:** 1-2 weeks
- **L:** 2-4 weeks
- **XL:** 1+ month (multi-sprint)

## Cross-references

- `00-summary.md` — TL;DR
- `axes/` — per-axis deep-dive
- `providers/` — per-engine analysis
- `README.md` — file index
