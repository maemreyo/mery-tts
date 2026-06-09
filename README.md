# Mery TTS Server

A **standalone, offline-first, local TTS server** — installable on any machine, connectable by any application over a versioned localhost API.

---

## What this is

A hybrid CLI + daemon that:

- Provides **local, offline TTS** via Piper-plus and Kokoro engine adapters
- Manages voice model downloads, integrity verification, and storage
- Exposes a versioned **REST + WebSocket API** on `localhost`
- Ships a `mery` CLI for synthesis, diagnostics, model management, and pairing
- Is independently installable, testable, and shippable without any specific client

## Who can use this

| Client type | How it connects | Example |
|---|---|---|
| Browser extension | `LocalhostTransport` → `/v1` | [Zam Reader](https://github.com/maemreyo/zreader) read-aloud, accessibility |
| Desktop app | HTTP client → `/v1` | Electron / Tauri / VS Code plugin / e-reader |
| CLI / script | `mery speak` or REST | Batch audio generation, terminal notifications |
| AI / LLM assistant | HTTP client → `/v1` | Ollama + Mery = fully local voice assistant |
| Home automation | HTTP client → `/v1` | Home Assistant TTS announcements |

---

## Quick start

**Prerequisites:** Python 3.11+ and `uv` (or `pipx`).

```bash
# Install uv if you don't have it yet (macOS / Linux):
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: winget install astral-sh.uv
# Alternative: brew install pipx && pipx ensurepath
```

```bash
# 1. Install Mery
uv tool install mery-tts-server
# or: pipx install mery-tts-server

# 2. Verify
mery doctor

# 3. Start the server (binds 127.0.0.1:8765 by default)
mery serve

# 4. Pair your client — prints a 6-char code for the client to claim
mery pair

# 5. Install English voices (ships with none by default)
mery voice-packs install pack.en-us

# 6. Synthesize
mery speak --text "Hello from Mery"
```

For the full AI-agent install contract (one link, hand it to an agent, it self-installs), see [`INSTALL_FOR_AGENTS.md`](INSTALL_FOR_AGENTS.md).

---

## Using with Zam Reader

Zam Reader is a browser extension that uses Mery for premium, offline read-aloud.

1. Install and start the server (steps 1–3 above)
2. Open any article → click the **audio button** in Zam Reader → select **Mery** as your voice source
3. The extension guides you through pairing and voice installation from there

If Mery is already running, the extension detects it automatically. Voice installation can also be done through the Mery Console at `http://127.0.0.1:8765/console/setup`.

---

## Status

Early runtime implementation. Core CLI/API, pairing, security, catalog, durable install lifecycle, OpenAI-compatible speech, packaged `/console` web UI, WAV export, and `make check` are implemented and tested. Real engine audio validation and signed app packaging remain future hardening work.

---

## Documentation

| Doc | Purpose |
|---|---|
| [`INSTALL_FOR_AGENTS.md`](INSTALL_FOR_AGENTS.md) | **One-link AI agent install contract** — paste to your agent, it self-installs |
| [`docs/integration/api-reference.md`](docs/integration/api-reference.md) | Full HTTP and WebSocket reference |
| [`docs/integration/integration-testing-guide.md`](docs/integration/integration-testing-guide.md) | Verified end-to-end guide with test coverage |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | System design, SoC, layer map |
| [`docs/adr/INDEX.md`](docs/adr/INDEX.md) | 35 Architecture Decision Records |
| [`docs/codebase/FOLDER_STRUCTURE.md`](docs/codebase/FOLDER_STRUCTURE.md) | Repo and package layout |

---

## Boundary rules

- No client **ever imports** Python server code
- No client **ever sends raw filesystem paths** to the server
- The server **never assumes any specific client** is the only consumer
- The server **never logs raw user text** in any diagnostic or log sink
- Model installs use **`modelId` only**, never raw URLs

---

## License

GPLv3. See `LICENSE`.
