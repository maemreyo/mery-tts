# Mery TTS Server

A **standalone, offline-first, local TTS server** — installable on any machine,
connectable by any application over a versioned localhost API.

Named *Mery* (from the creator's handle **zamery**) — a merry voice that lives
entirely on your device.

> **First-party client:** [Zam Reader](../zreader/) — a browser extension for
> reading English content. Zam Reader integrates through the `/v1` bridge contract.
> Mery is designed from the start for any client, not only Zam Reader.

---

## What this is

A hybrid CLI + daemon that:

- Provides high-quality **local, offline TTS** via Piper-plus and Kokoro engine adapters
- Manages voice model downloads, integrity verification, and storage
- Exposes a versioned **REST + WebSocket API** on `localhost` — any app can connect
- Ships a `mery` CLI for manual synthesis, diagnostics, model management, and pairing
- Is independently installable, testable, and shippable without any specific client

---

## Who can use this

Mery is a **generic local TTS infrastructure layer**. The `/v1` API is plain
HTTP + WebSocket — any application on the same machine can pair and use it:

| Client type | How it connects | Example use case |
|---|---|---|
| Browser extension | `LocalhostTransport` → `/v1` | Zam Reader read-aloud, accessibility extensions |
| Desktop app | HTTP client → `/v1` | Electron/Tauri notes app, VS Code plugin, e-reader |
| CLI / script | `mery speak` or REST | Batch audiobook generation, terminal notifications |
| AI / LLM assistant | HTTP client → `/v1` | Ollama + Mery = fully local voice assistant |
| Home automation | HTTP client → `/v1` | Home Assistant TTS announcements |

See [`docs/use-cases.md`](docs/use-cases.md) for the full breakdown.

---

## Status

> Early runtime implementation. Core CLI/API scaffolding, pairing, local security controls, catalog/voice fixtures, durable install lifecycle, OpenAI-compatible speech, packaged `/console` web UI, WAV export, and the local `make check` gate are implemented and tested. Real engine audio validation and signed app packaging remain future hardening work.

- [x] Design decisions finalized (27 decisions, see `docs/reports/local-tts-helper-design-decisions.md`)
- [x] Readiness contract defined (see `docs/integration/zam-reader-readiness-contract.md`)
- [x] Engine research complete (see `docs/reports/local-tts-solutions-research.md`)
- [x] Architecture backbone docs (see `docs/architecture/`)
- [x] ADRs 0001–0012 (see `docs/adr/`)
- [x] Early runtime implementation slices
- [ ] Real engine adapters audio validation (Piper-plus, Kokoro)
- [x] REST + WebSocket API scaffolding and core contract tests
- [x] Packaged local web console served at `/console` by `mery serve`
- [x] CLI (`mery`) core commands and local export path
- [x] Core test suite and `make check` gate
- [x] Phase 1 packaging-agnostic runtime smoke coverage

---

## Quick start — Phase 1 early access

Phase 1 early access requires Terminal. Install with either `uv` or `pipx`, then run the first-run diagnostics and pairing commands locally. The packaged core starts one FastAPI server, serves `/v1` plus the local web console at `/console`, and supports deterministic CLI/API/web smoke paths without optional engine downloads; the bundled catalog and console assets are Python package resources and can be browsed offline. Explicit model installation and remote catalog refresh are separate user-triggered network actions, and real Piper-plus or Kokoro audio requires installing the matching optional engine extra and remains gated by real-runtime validation.

```bash
# Install with uv
uv tool install mery-tts-server
# or install with pipx
pipx install mery-tts-server

# Check environment
mery doctor

# Start server; open the local web console at http://127.0.0.1:<port>/console
mery serve

# Pair a client or paste the bearer token into /console (from a second terminal)
mery pair

# Install a voice model
mery models install piper-plus.en-us.lessac.medium

# Submit text through the CLI stub path
mery speak --text "Hello from Mery"

# Export deterministic local WAV audio without optional engine downloads
mery speak --file input.txt --output hello.wav
```

---

## Documentation index

| Document | What it covers |
|---|---|
| [`docs/use-cases.md`](docs/use-cases.md) | Generic use cases — who can use Mery and how |
| [`docs/zam-reader-context.md`](docs/zam-reader-context.md) | What Zam Reader is and why Mery exists |
| [`docs/codebase/FOLDER_STRUCTURE.md`](docs/codebase/FOLDER_STRUCTURE.md) | Annotated repo + package layout |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | System design, SoC, layers, module boundaries |
| [`docs/codebase/TECH_STACK.md`](docs/codebase/TECH_STACK.md) | Packages, logging strategy, DevEX, UX patterns |
| [`docs/adr/INDEX.md`](docs/adr/INDEX.md) | Architecture Decision Records index (ADR-0001–0012) |
| [`docs/integration/zam-reader-readiness-contract.md`](docs/integration/zam-reader-readiness-contract.md) | Requirements before Zam Reader may use Mery |
| [`docs/reports/local-tts-helper-design-decisions.md`](docs/reports/local-tts-helper-design-decisions.md) | Full 27-decision design log |
| [`docs/reports/local-tts-solutions-research.md`](docs/reports/local-tts-solutions-research.md) | Engine research and benchmarks |
| [`docs/reports/phase-1-smoke-and-tests.md`](docs/reports/phase-1-smoke-and-tests.md) | Live-server smoke test, full pytest run, and `make check` gate evidence |

---

## Architecture in one diagram

```text
┌──────────────────────────────────────────────────────────────────┐
│  Any client — browser extension, desktop app, CLI script, LLM   │
│  Connects via: HTTP REST + WebSocket /v1 (localhost only)        │
└───────────────────────────┬──────────────────────────────────────┘
                            │  /v1 REST + WebSocket (localhost only)
┌───────────────────────────▼──────────────────────────────────────┐
│  mery-tts-server                                                 │
│                                                                  │
│  CLI (mery)              API (FastAPI + uvicorn)                 │
│    serve / pair            /v1/health, /v1/engines               │
│    doctor                  /v1/voices, /v1/catalog               │
│    engines / voices        /v1/models, /v1/storage               │
│    models / storage        /v1/diagnostics, /v1/pair             │
│    speak [--text|--file --output] WS /v1/events                  │
│                            /console packaged local web console   │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐     │
│  │EngineRegistry│  │  ModelManager  │  │ CatalogManager   │     │
│  │  PiperPlus   │  │  installer     │  │  bundled catalog │     │
│  │  Kokoro      │  │  verifier      │  │  remote refresh  │     │
│  └──────────────┘  └────────────────┘  └──────────────────┘     │
│                                                                  │
│  Security: token auth · origin allowlist · rate limits          │
│  Storage:  ~/Library/Application Support/Mery TTS/ (macOS)      │
│  Logging:  structlog · JSON in prod · console in dev            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Boundary rules (non-negotiable)

- No client **ever imports** Python server code
- No client **ever sends raw filesystem paths** to the server
- No client **ever calls `fetch('http://127.0.0.1:...')`** directly from untrusted code — always route through a transport abstraction
- The server **never assumes any specific client** is the only consumer
- The server **never logs raw user text** in any diagnostic or log sink
- Model installs use **`modelId` only**, never raw URLs from any client

---

## License

GPLv3. See `LICENSE`.
