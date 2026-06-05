# Axis 03 — Ecosystem

**Last updated:** 2026-06-05
**Status in roadmap:** Explicit
**Sub-items:** Client SDKs, Model registry, Native bridge

---

## What this axis covers

The external surface of Mery beyond the protocol itself: SDKs for common languages, the community voice catalog, and alternative transports. This axis is what turns Mery from "a TTS server" into "a TTS platform."

## Sub-items

### 3.1 Client SDKs

**What it is:** First-party libraries in TypeScript, Python, Go, Swift, etc. that wrap Mery's `/v1` contract. Goal: zero-friction integration for any client app.

**Why it matters:**
- Each SDK lowers the integration cost for that language community
- Zam Reader is TS — TS SDK is the most important
- Tier 1 BASE for any "platform" claim in 2026 (every cloud TTS has SDKs in 5+ languages)
- Reduces "I have to write my own HTTP client" friction

**Cost:**
- High if hand-written and maintained per language
- **Recommendation: generate from OpenAPI** with Orval (TypeScript-first) + Speakeasy/Stainless for others
- Hand-written: streaming layer (Orval doesn't auto-generate WebSocket from OpenAPI)
- Maintenance: SDK version drift when protocol evolves (need CI to fail if SDK doesn't match spec)

**Tier:** Tier 1 BASE for "I want a platform" claim; Tier 2 COMMON for "I want adoption."

**Reference SDKs (good patterns to study):**
- [OpenAI Node SDK](https://github.com/openai/openai-node) — `client.audio.speech.create()`, `Speech` object (file/stream)
- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js) — `.generate()`, `.stream()`, `.play()`
- [Azure Speech SDK](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/) — `SpeechSynthesizer`, `PullStream` for streaming
- [Coqui TTS Python API](https://docs.coqui.ai/en/stable/inference.html) — `tts()`, `tts_to_file()`, `list_models()`
- [LiveKit Agents TTS](https://github.com/livekit/agents) — `tts.TTS`, `StreamAdapter`, `TTSCapabilities` dataclass
- [Soniox Web SDK](https://soniox.com/docs/sdk/web-SDK/tts/realtime-speech-generation) — WebSocket TTS, async iterable chunks
- [RealtimeTTS](https://koljab.github.io/RealtimeTTS/en/usage/) — `TextToAudioStream`, `on_audio_chunk` callback

**SDK design checklist:**
- [ ] Promise-based async/await
- [ ] Streaming-first (`stream()` returns async iterable)
- [ ] Cancellation (`cancel()` / `abort()`)
- [ ] Word-boundary callbacks
- [ ] Format flexibility (PCM16, MP3, WAV)
- [ ] Retry with backoff for transient failures
- [ ] Optional playback integration (Web Audio API for browser)

**SDK generation tools (compare):**
| Tool | Streams | React Query | Zod | Best for |
|---|---|---|---|---|
| **Orval** | ✅ (custom mutator) | ✅ Built-in | ✅ | TS SDK + React hooks |
| **openapi-typescript** | ❌ Types only | ❌ | ❌ | Thin types layer |
| **@hey-api/openapi-ts** | Partial | Via plugin | ✅ | SDK with interceptors |
| **Kubb** | ✅ | Plugin | ✅ | Plugin pipeline |
| **Stainless** (commercial) | ✅ | N/A | ✅ | Production-grade |

**Recommendation:**
- **TypeScript SDK**: Orval + custom WebSocket mutator + Zod validators
- **Python SDK**: hand-written (small surface, asyncio, websockets library)
- **Go SDK**: hand-written (gorilla/websocket or stdlib)
- **Other languages**: only if community demand

**Streaming layer in generated SDKs:** OpenAPI doesn't natively describe WebSocket. Pattern: generate REST types/functions, then add hand-written `stream()` function. Soniox does this.

**Priority: P2** — build after `/v1` contract is stable. TS first (Zam Reader).

---

### 3.2 Model registry / community catalog

**What it is:** A versioned, signed, distributed catalog of community-contributed voice models. Users can `mery pull jane-doe/en_US-female-narrator` to download a voice. Similar to `ollama pull llama3`.

**Why it matters:**
- **"Ollama for TTS"** — this is half of the strategic horizon (the other half is OpenAI compat)
- Flywheel: more voices → more users → more contributions
- Tier 1 BASE for "TTS platform" claim
- Without this, Mery is a server. With this, Mery is an ecosystem.

**Cost:**
- Very high:
  - **Hosting**: TTS models 60-350MB. 100 voices = 30GB. With downloads, bandwidth is real cost.
  - **CDN**: Cloudflare R2 (zero egress) or S3+CloudFront
  - **Signing**: Ed25519 keys (Ollama-compatible pattern), Sigstore/cosign for attestation
  - **Moderation**: license tracking, content moderation, deepfake detection
  - **Governance**: takedown process, DMCA, consent records
  - **Format standardization**: ONNX primary, GGUF emerging
  - **Discovery**: web catalog (UI), CLI search, community ratings
- **Cost economics at scale:**
  - Startup (100 voices, 1K downloads/day): ~$150-300/mo
  - Growth (500 voices, 10K downloads/day): ~$1.5k-3k/mo
  - Scale (2000 voices, 100K downloads/day): ~$15k-30k/mo

**Reference architecture (Ollama's pattern — gold standard):**
```
~/.ollama/models/
├── manifests/
│   └── registry.ollama.ai/library/llama3/latest   # JSON manifest
└── blobs/
    ├── sha256-abc123...                            # Model weights (GGUF)
    ├── sha256-def456...                            # Config layer
    ├── sha256-ghi789...                            # Template layer
    ├── sha256-jkl012...                            # Parameters
    └── sha256-mno345...                            # License
```

**Voice manifest schema (Mery proposal):**
```yaml
name: jane-doe/en_US-female-narrator
version: 1.0.0
namespace: jane-doe
author:
  name: Jane Doe Voice Studio
  contact: jane@example.com
license: CC-BY-4.0
languages: [en_US]
gender: female
styles: [narration, podcast]
format: onnx  # or gguf, pytorch
size_bytes: 471859200
sample_rate: 24000
base_model: coqui/XTTS-v2
consent:
  type: synthetic  # or cloned
  reference_audio_sha256: abc123...
  consent_record_url: https://...
  scopes: [commercial_use, educational_use]
  expiration: 2028-01-01
tags: [english, american, female, natural]
ratings:
  quality_score: 4.5
  naturalness: 4.7
```

**Lifecycle states:**
- `draft` → not published
- `pending_review` → awaiting moderation
- `active` → publicly available
- `deprecated` → old version, pull warns
- `taken_down` → moderation action, archive only

**Pull/push flow (Ollama-inspired):**
```
$ mery pull jane-doe/en_US-female-narrator
  ✓ Downloading manifest
  ✓ Verifying voice consent
  ✓ Downloading model (450MB)
    45% [████████████████░░░░] 203MB/s
  ✓ Downloading reference audio
  ✓ Verifying checksum
  ✓ Installing voice profile

$ mery speak --voice jane-doe/en_US-female-narrator "Hello, world!"
```

**Voice cloning in catalog — HARD:** if community catalog allows cloned voices, need:
- Consent records (linked from manifest)
- Reference audio SHA256 (for verification)
- Scope tracking (commercial? educational? which geographies?)
- Takedown flow (DMCA + voice actor revocation)
- Deepfake detection at upload (AudioSeal, voice encoder verification)
- EU AI Act disclosure metadata

**Reference projects:**
- [ollama/ollama](https://github.com/ollama/ollama) — OCI-inspired manifest + blob storage, 7 layer types
- [huggingface hub](https://huggingface.co/docs/hub/en/model-cards) — Git + LFS, model cards, gated models
- [spdxai/spdx-3-model](https://spdxai.github.io/) — SPDX 3.0 AI Profile for license tracking
- [veritaschain/cap-spec](https://github.com/veritaschain/cap-spec) — CAP spec for voice consent/provenance
- [C2PA](https://c2pa.org/) — content authenticity standard (emerging for audio)
- [Meta AudioSeal](https://github.com/facebookresearch/audioseal) — inaudible watermarking

**Hidden risks (the 5 that can kill the feature):**
1. **Deepfake without consent** = legal liability + brand destruction
2. **Copyrighted voices** (e.g., Scarlett Johansson's voice) = lawsuit
3. **Bandwidth costs** at scale — not a tech problem, a finance problem
4. **Moderation staff** — humans needed, not just automation
5. **Trust** — one bad clone in catalog = community backlash

**Recommendation:** **P0 strategic** — but **ship MVP with synthetic-only voices first.** Add cloned-voice support only after governance ADR is in place. This is the same sequencing as ElevenLabs (which launched with stock voices, added cloning later with strict consent verification).

---

### 3.3 Native bridge (Native Messaging transport)

**What it is:** Replace the HTTP localhost transport with Chrome/Firefox Native Messaging (stdin/stdout JSON over OS-level pipe). Hosted by a small native binary on the user's machine.

**Why it matters:**
- No open port (better firewall UX)
- Extension ID allowlist (tighter security model)
- Used by password managers: Bitwarden, 1Password

**Cost:**
- High:
  - Native binary per OS (Windows, macOS, Linux)
  - Per-browser manifest files (different formats: `allowed_origins` for Chromium, `allowed_extensions` for Firefox)
  - Manifest installation per-user (registry on Windows, `~/.mozilla/native-messaging-hosts/` on Linux)
  - Dev iteration slower (no hot-reload, OS-level debugging)
  - First message limit: 1 MiB host→browser, 64 MiB browser→host

**Local-LLM precedent:**
- **Ollama**: HTTP localhost (port 11434) — no Native Messaging
- **LM Studio**: HTTP localhost (port 1234) — no Native Messaging
- **llama.cpp server**: HTTP localhost (port 8000) — no Native Messaging
- **LocalAI**: HTTP localhost (port 8080) — no Native Messaging
- **Bitwarden / 1Password**: Native Messaging — but these are extension ↔ desktop app, not extension ↔ server

**Conclusion:** HTTP localhost is the established pattern. Native Messaging is for extension ↔ desktop app (where the desktop owns state like a vault). Mery is a server, not a vault.

**Reference:**
- [Chrome Native Messaging spec](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)
- [Firefox Native Messaging](https://wiki.mozilla.org/WebExtensions/Native_Messaging)
- [Bitwarden BrowserApi](https://github.com/bitwarden/clients/tree/main/apps/browser) — cross-browser extension architecture
- [1Password browser security](https://support.1password.com/1password-browser-security/) — Native Messaging + WebSocket fallback

**When to add Native Messaging:**
- Chrome Web Store rejects HTTP localhost extensions (hasn't happened yet)
- User explicitly requests it
- Mery needs to be auto-launched by browser (vs manually by user)
- OS integration needed (e.g., read system audio devices)

**Recommendation:** **P3 defer.** The current LocalhostTransport in ARCHITECTURE.md is fine. Reconsider only if a Chrome/Firefox store policy change requires it.

---

## Tier mapping (per sub-item)

| Sub-item | Tier | Mery's priority | ADR needed? |
|---|---|---|---|
| Client SDKs | Tier 1 BASE (platform) / Tier 2 COMMON (adoption) | P2 (TS first) | Maybe (per language) |
| Model registry | Tier 1 BASE (TTS platform claim) | **P0 (synthetic-only MVP)** | **Yes (governance + format + CDN)** |
| Native bridge | Tier 3 PROVIDER-SPECIFIC | P3 defer | Maybe (only if policy forces) |

## The "Ollama for TTS" chain (validation)

```
OpenAI compat (axis 02)  +  Model registry (axis 03)
   ↓                              ↓
"any tool talks to Mery"     "any voice available for Mery"
   ↓                              ↓
            "Ollama for TTS"
                  ↓
     install mery → kéo voice → use anywhere
```

Both halves needed. OpenAI compat without catalog = server with no community. Catalog without compat = community nobody can use.

**Strategic horizon validated.** This is the right endgame.

## Cross-references

- `axes/02-protocol.md` — OpenAI compat (the other half of the chain)
- `axes/05-governance-and-licensing.md` — voice cloning policy (gates community catalog)
- `axes/06-operations-and-observability.md` — CDN, bandwidth, ops
- `providers/` — voice models to potentially catalog
- `99-priority-matrix.md` — sequencing
