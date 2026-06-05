# Mery TTS Server — Generic Use Cases

Mery is not tied to any specific client application. It is a **local TTS
infrastructure layer**: any application on the same machine can pair with it
and use its REST + WebSocket API to synthesize speech, manage voice models,
and run diagnostics.

The design principle is stated explicitly in ADR-0001:

> *"Other future clients could use the helper without any Zam Reader dependency."*

This document maps the generic use cases that the architecture already supports
or can support with minimal extension.

---

## Client categories

### 1. Browser extensions

The `/v1` API was designed with browser extensions as the primary client
(Zam Reader is the first-party example), but the protocol is
extension-agnostic. Any extension can implement a `LocalhostTransport`
bridge to connect.

| Use case | What Mery provides |
|---|---|
| Read-aloud for web articles | `synthesize.request` → streaming PCM16 audio chunks |
| Language learning pronunciation | Single-word synthesis at low latency |
| Accessibility / screen reader | Full synthesis with word-boundary events (future) |
| English learning tool | Voice quality choice: lightweight (Piper-plus) vs quality (Kokoro) |
| RSS / news reader extension | Synthesize article text offline, no cloud API |

**What the extension must implement:** a transport adapter
(`LocalhostTransport`), audio renderer, and pairing UI. Mery provides
everything else.

---

### 2. Desktop applications

Electron, Tauri, and other native desktop frameworks can call `localhost:8765`
directly from their main process or a worker thread. No browser extension
sandbox restrictions apply.

| Use case | Notes |
|---|---|
| Note-taking app read-aloud (Obsidian, Logseq) | Plugin calls `/v1/events` WS for streaming |
| E-reader TTS (Calibre, FBReader) | REST to select voice, WS to stream |
| VS Code extension — read docs aloud | Simple REST `POST /v1/speak` path |
| IDE accessibility tool | Word-boundary events for cursor-sync (future) |
| Chat / messaging app — read messages | Queue synthesize requests, cancel on new message |

**Advantage over embedding an engine directly:** the app never needs to
manage model downloads, storage, or checksums. Mery handles all of that;
the app only calls the API.

---

### 3. CLI / shell scripting

The `mery speak` command and the REST API are both usable from shell scripts,
CI pipelines, or any automation tool.

```bash
# Terminal notification on long build finish
make build && mery speak --text "Build complete" --play

# Batch convert text files to audio (file export — future extension)
for f in chapters/*.txt; do
  mery speak --file "$f" --output "${f%.txt}.wav"
done

# Synthesize a line and pipe raw PCM to another tool
mery speak --text "Hello" --format raw | ffmpeg -f s16le -ar 22050 -i - out.mp3
```

The `mery speak --output <file>` path is a natural extension of ADR-0012
(audio delivery mode) — a third sink beyond `--play` and WebSocket streaming,
requiring no changes to the engine layer.

---

### 4. Local AI / LLM voice output

The combination of a local LLM (Ollama, LM Studio, llama.cpp) and a local TTS
server creates a **fully offline, zero-cloud voice assistant**:

```text
User speaks
  → Whisper (local STT)
  → Ollama / local LLM (generates response text)
  → Mery TTS Server (synthesizes response)
  → System speakers
```

Mery's streaming WebSocket protocol (`audio.chunk` events) is ideal here
because the LLM can start feeding text to Mery before it finishes generating —
enabling low-latency first-word playback.

Open-source frontends (Open WebUI, Jan.ai, etc.) could integrate Mery as a
drop-in local TTS backend, replacing their current cloud-TTS dependency.

---

### 5. Home automation

Home Assistant and similar platforms need TTS for local announcements
("Laundry is done", "Front door opened"). Cloud TTS adds latency and a
network dependency for time-sensitive events.

Mery running on the same machine as the home automation hub provides:
- Offline-first TTS (works during internet outages)
- Low-latency local synthesis
- No per-character cloud billing
- Voice model management through the same `mery` CLI

A Home Assistant custom component would call `POST /v1/events` (WebSocket)
or a simple REST endpoint and stream audio to a media player entity.

---

### 6. Content creation / batch voiceover

Writers, educators, and content creators who produce video or podcast content
can use Mery to generate high-quality offline voiceovers:

```bash
# Generate chapter narration
mery speak --file chapter-03.md --voice kokoro.en-us.af_heart --output chapter-03.wav

# Multi-voice dialogue (future: voice-per-line via manifest)
mery batch --manifest dialogue.json --output-dir audio/
```

This use case motivates the `--output` file export mode described in
ADR-0012 and benefits directly from the model quality choices (Kokoro for
natural English narration, Piper-plus for fast draft passes).

---

## What changes for a fully generic deployment

Mery's architecture already supports all the above use cases. The only
Zam Reader–specific assumptions that would need generalizing for a fully
neutral deployment are:

| Current assumption | Generic equivalent |
|---|---|
| Bundled catalog is Vietnamese/English-curated | Catalog becomes locale-configurable or community-sourced |
| Pairing flow designed for one primary client | Multi-client pairing (multiple apps can hold long-lived tokens) |
| `docs/integration/` contains only the Zam Reader contract | Additional per-client readiness contracts added here |
| `docs/zam-reader-context.md` explains the first-party client | Additional `docs/<client>-context.md` files for each integrator |

The core engine, API, model manager, catalog, security, and storage layers
require **zero changes** to serve any of the clients listed above.

---

## Related

- [ADR-0001](adr/ADR-0001-product-boundary.md) — why the server is standalone,
  and why no specific client is assumed
- [ADR-0005](adr/ADR-0005-api-protocol.md) — the REST + WebSocket contract
  that all clients use
- [ADR-0012](adr/ADR-0012-audio-delivery-mode.md) — how audio delivery
  works for CLI vs streaming clients, and the future file-export sink
- [ADR-0009](adr/ADR-0009-pairing-flow.md) — how clients authenticate
- [`docs/integration/zam-reader-readiness-contract.md`](integration/zam-reader-readiness-contract.md) — example of a per-client integration contract
