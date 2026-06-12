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

# Optional: open the guided launcher for common actions
mery launch

# 3. Start the server (binds 127.0.0.1:8765 by default and prints next commands before blocking)
mery serve

# 4. Pair your client — prints a 6-char code, setup URL, and suggested next commands
mery pair

# 5. Review and install English voices (ships with none by default)
mery launch --action install-baseline-voice --json
mery launch --action install-baseline-voice --yes --json

# 6. Synthesize
mery speak --text "Hello from Mery"
mery speak --file input.txt --output hello.wav
```

For a guided terminal experience, install the optional interactive extra and run the launcher:

```bash
uv tool install "mery-tts-server[interactive]"
mery launch
mery launch --list-actions
mery launch --action readiness --json
```

The launcher keeps `mery` scriptable: bare `mery` still shows CLI help, while `mery launch` is the guided entrypoint for setup readiness, status, Console, pairing, setup URLs, local help, and developer checks when running from a repo checkout. Direct setup/onboarding commands such as `mery serve`, `mery pair`, `mery setup url`, and `mery setup recommend` may print concise suggested next commands so terminal users can continue without opening the launcher. The P1 setup path uses the packaged bundled catalog by default: `mery launch --action install-baseline-voice --json` displays the baseline pack/model id, provider, locale, source kind, approximate size, license/provenance, and capability impact without downloading anything; add `--yes` only after reviewing that metadata to start the durable install job.

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

Phase 1 early access runtime. Core CLI/API, pairing, security, catalog, durable install lifecycle, OpenAI-compatible speech, WAV export, launcher readiness, sanitized support bundles, stable recovery actions, package-manager-owned upgrades, safe repair policy, and `make check` are implemented and tested. P1 ships as a budget-limited Python tool install through `uv tool` or `pipx` on one package release channel; native signed installers, OS services/autostart, release channels, and built-in self-update are deferred. The package serves `/v1` plus the local web console at `/console` without optional engine downloads because the bundled catalog and console assets are Python package resources. Explicit model installation and remote catalog refresh remain separate user-triggered network actions; real Piper-plus or Kokoro audio requires installing the matching optional engine extra and remains gated by real-runtime validation. Language support is model-dependent and exposed through installed/catalog voice locale metadata, not a universal runtime claim.

---

## Documentation

| Doc | Purpose |
|---|---|
| [`INSTALL_FOR_AGENTS.md`](INSTALL_FOR_AGENTS.md) | **One-link AI agent install contract** — paste to your agent, it self-installs |
| [`docs/integration/api-reference.md`](docs/integration/api-reference.md) | Full HTTP and WebSocket reference |
| [`docs/integration/integration-testing-guide.md`](docs/integration/integration-testing-guide.md) | Verified end-to-end guide with test coverage |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | System design, SoC, layer map |
| [`docs/adr/INDEX.md`](docs/adr/INDEX.md) | Architecture Decision Records through ADR-0050 |
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
