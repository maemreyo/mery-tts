# Axis 02 — Protocol

**Last updated:** 2026-06-05
**Status in roadmap:** Explicit
**Sub-items:** TTFB streaming, SSML markup, OpenAI compat

---

## What this axis covers

The protocol surface that Mery exposes to clients. ADR-0005 defined the hybrid REST + WebSocket contract. This axis covers the **next-level** protocol capabilities that turn Mery from a working local helper into a drop-in replacement for cloud TTS.

## Sub-items

### 2.1 TTFB streaming (Time to First Byte / First Audio)

**What it is:** Minimize the latency between client sending `synthesize.request` and receiving the first `audio.chunk` event. Target: ≤300ms P50, ≤500ms P95.

**Why it matters:**
- LLM-voice use case (Ollama + Mery = voice assistant): the LLM streams tokens, Mery starts synthesizing as text arrives, user hears first word as soon as possible
- ADR-0012 already chose hybrid delivery (CLI direct / WS streaming) — this is the WS-mode latency
- Tier 1 BASE for any "real-time" TTS in 2026

**Cost:**
- Medium. Need:
  - Streaming-capable engine (kokoro-onnx is batch-only — needs "prefill + first-chunk-fast" trick)
  - Pre-warmed models (no cold-start penalty)
  - Engine-specific tuning: prefill first sentence while waiting for next
- Need SLA definition: ≤300ms P50 first chunk, ≤500ms P95
- Need contract test: assert TTFB on reference inputs

**Tier:** Tier 1 BASE for realtime; Tier 2 COMMON otherwise.

**Reference projects:**
- [ElevenLabs Flash](https://elevenlabs.io/) — ~90ms latency (cloud reference)
- [Cartesia](https://docs.cartesia.ai/) — ~100ms TTFB
- [Inworld](https://inworld.ai/) — <200ms median
- [Qwen3-TTS on Replicate](https://replicate.com/qwen/qwen-tts) — ~97ms first packet
- [CosyVoice 2](https://github.com/FunAudioLLM/CosyVoice) — 150ms TTFA, unified streaming/non-streaming
- [Fish Audio S2](https://github.com/fishaudio/fish-speech) — ~100ms TTFA via SGLang

**Hidden risk:** Some engines are batch-only (kokoro-onnx without SGLang wrapper). Need to either: (a) swap engine, (b) wrap with prefill-then-chunk strategy, (c) accept higher latency for that engine.

---

### 2.2 SSML markup (Speech Synthesis Markup Language)

**What it is:** Allow clients to send SSML-formatted text instead of plain text. W3C standard since 2010 (SSML 1.1).

**Why it matters:**
- Standard for content creators / accessibility / language learning
- Tags: `<speak>`, `<break>`, `<prosody>`, `<say-as>`, `<sub>`, `<voice>`, `<phoneme>`, `<mark>`
- Allows precise control over pauses, emphasis, pronunciation
- Tier 2 COMMON (most cloud providers support full SSML)

**Cost:**
- Medium-high:
  - **SSML parser**: detect `<speak>` root, parse tags
  - **Engine mapping**: piper-plus (limited), Kokoro (preprocessed), Coqui (none)
  - **Fallback policy**: if engine doesn't support a tag, what happens? Silent drop? Error? Fallback to plain text?
  - **Diagnostic pain**: users will debug "why isn't my SSML working" — feature fragmentation
- Recommendation: preprocess SSML to Mery-native signals, then synthesize plain text. This way, SSML works uniformly without per-engine mapping.

**Tier:** Tier 2 COMMON (in cloud world). Tier 3 PROVIDER-SPECIFIC in local-engine world (Piper/Coqui don't support).

**Reference projects:**
- [W3C SSML 1.1 spec](https://www.w3.org/TR/speech-synthesis11/)
- [Google Cloud TTS SSML tutorial](https://docs.cloud.google.com/text-to-speech/docs/ssml-tutorial)
- [Azure Speech SSML](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup)
- [ElevenLabs audio tags](https://elevenlabs.io/docs/voices/voice-design/audio-tags) (proprietary alternative)
- [Piper SSML Issue #275](https://github.com/rhasspy/piper/issues/275) (still open)
- [Coqui TTS SSML Issue #752](https://github.com/coqui-ai/TTS/issues/752), [#3436](https://github.com/coqui-ai/TTS/issues/3436) (rejected as out-of-scope)

**Hidden risk:** SSML tags the engine doesn't understand = silent drop OR error. Either way, users will be confused. Need a clear fallback policy documented.

**Recommendation:** **DEFER SSML** until engines upstream support it better. Engines local support SSML poorly. Preprocessing layer is feasible but adds maintenance burden. Build only if user demand materializes.

---

### 2.3 OpenAI API compatibility (drop-in replacement)

**What it is:** Implement OpenAI's `/v1/audio/speech` endpoint as a Mery route. Mery's existing `/v1` contract stays; OpenAI compat is added as either a separate path or via header detection.

**Why it matters:**
- **Distribution hack.** Open WebUI, Jan.ai, Continue.dev, litellm, OpenAI Python SDK — all consume OpenAI TTS API. Mery with compat = instant user base with zero integration cost.
- Strategic horizon: "Ollama for TTS" requires this. The community catalog is half the story; compat is the other half.
- Tier 1 BASE in the sense that "compatibility with OpenAI" is the de facto universal protocol for TTS in 2026.

**Cost:**
- Medium:
  - Schema mapping: `model` → engine, `voice` → Mery voice ID (mapping file)
  - Format mapping: `response_format` (`mp3`/`opus`/`aac`/`flac`/`wav`/`pcm`) → Mery output format
  - Auth mapping: `Authorization: Bearer <openai_key>` → Mery's per-install token (transparent proxy)
  - Streaming: `stream_format: "sse" | "audio"` → Mery WS or chunked HTTP
  - **Path collision**: OpenAI uses `/v1/audio/speech` which conflicts with Mery's `/v1` namespace
- Need a `voices.yaml` mapping: `alloy → mery_voice_neutral_1`, `coral → mery_voice_female_1`, etc.
- litellm pattern: model routing, voice mapping, extra_body for provider-specific

**OpenAI's current API surface (gpt-4o-mini-tts):**
- Models: `tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`, `gpt-4o-mini-tts-2025-12-15`
- Voices: `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`, `verse`, `marin`, `cedar` (13 total)
- Output formats: `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm`
- Streaming: `stream_format: "sse" | "audio"` (only on gpt-4o-mini-tts)
- Auth: `Authorization: Bearer <key>`
- Max input: 4096 chars
- Speed: 0.25 → 4.0

**Tier:** Tier 1 BASE for distribution, Tier 2 COMMON for any TTS server claiming "modern" status.

**Reference projects:**
- [matatonic/openedai-speech](https://github.com/matatonic/openedai-speech) — Coqui XTTS + Piper, OpenAI-compat
- [Kamil-Krawiec/piper-tts-http-server](https://github.com/Kamil-Krawiec/piper-tts-http-server) — Piper with OpenAI compat
- [Kitten-TTS-Server](https://github.com/) — OpenAI-compat, GPU
- [litellm TTS proxy](https://docs.litellm.ai/docs/text_to_speech) — multi-provider OpenAI proxy
- [Coqui TTS server](https://coqui-tts.readthedocs.io/en/latest/server.html) — has OpenAI-compat endpoint

**Architecture options:**

```text
Option A: Separate path (recommended)
  POST /openai/v1/audio/speech   → OpenAI compat shim
  POST /v1/audio/speech         → Mery native (ADR-0005)

Option B: Header detection
  POST /v1/audio/speech
  X-Mery-Mode: compat  → OpenAI compat handler
  (no header)          → Mery native

Option C: Model prefix
  POST /v1/audio/speech
  model: "tts-1"       → OpenAI compat
  model: "mery-fast"   → Mery native
```

**Recommendation:** **Option A (separate path)** — cleanest, no collision, easy to version independently.

**Voice mapping example (from litellm):**
| OpenAI voice | Polly | Coqui |
|---|---|---|
| alloy | Joanna | p225 |
| echo | Matthew | p234 |
| fable | Amy | p245 |
| onyx | Brian | p258 |
| nova | Ivy | p270 |
| shimmer | Kendra | p304 |

Mery needs a similar `voices.yaml` that maps each OpenAI voice to a Mery engine + voice ID, configurable per engine.

**Hidden risks:**
- OpenAI will add new fields/voices. Mery's compat shim must decide: follow or pin version?
- Streaming differs: OpenAI uses SSE or binary chunked; Mery uses WebSocket. Need to translate.
- Some OpenAI features (style `instructions`, Realtime API) are gpt-4o-mini-tts specific. Map to Mery's extensions or stub.

**Priority: P0** — highest leverage move in the entire roadmap.

---

## Tier mapping (per sub-item)

| Sub-item | Tier | Mery's priority | ADR needed? |
|---|---|---|---|
| TTFB streaming | Tier 1 BASE (realtime) / Tier 2 COMMON | **P1** | Yes (SLA + streaming engine contract) |
| SSML markup | Tier 2 COMMON (cloud) / Tier 3 PROVIDER-SPECIFIC (local) | **P3 defer** | Maybe (only if user demand) |
| OpenAI compat | Tier 1 BASE (distribution) | **P0** | Yes (path, voice mapping, format mapping) |

## Streaming protocol comparison (relevant to TTFB streaming)

| Protocol | Latency | Bidirectional | Best for |
|---|---|---|---|
| **WebSocket** | ~100ms | ✅ | Realtime, multi-turn (Mery's choice per ADR-0005/0012) |
| **SSE** | ~150ms | ❌ | Simple streaming, OpenAI compat |
| **HTTP chunked** | ~150ms | ❌ | Basic progressive download |
| **WebTransport** | ~300-500ms (HTTP/3) | ✅ | Future, multi-stream, no head-of-line blocking |
| **WebRTC** | ~200-500ms | ✅ | Overkill for one-way TTS |
| **gRPC-web** | ~200ms | ✅ | Overkill, requires proxy |

Mery's choice (WebSocket per ADR-0005) is **right**. SSE is needed only for OpenAI compat shim.

## Cross-references

- `axes/03-ecosystem.md` — Model registry + Client SDKs (the "Ollama for TTS" chain)
- `axes/06-operations-and-observability.md` — SLA targets, metrics for TTFB tracking
- `99-priority-matrix.md` — sequencing
