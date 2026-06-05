# Zam Local TTS Helper

Standalone local TTS helper app for [Zam Reader](../zreader/).

This repo is intentionally separate from `zreader` so the helper can have its own
Python runtime, packaging, model management, CI, and release lifecycle.
Zam Reader integrates with it **only through a versioned `/v1` bridge contract** —
never by importing Python internals.

---

## What this is

A hybrid CLI + daemon app that:

- Provides high-quality **local, offline TTS** via Piper-plus and Kokoro engine adapters
- Manages voice model downloads, integrity verification, and storage
- Exposes a versioned **REST + WebSocket API** on localhost for Zam Reader
- Ships a `zam-tts` CLI for manual testing, diagnostics, and pairing
- Is independently installable, testable, and shippable without Zam Reader

---

## Status

> Design/bootstrap phase. No runtime implementation yet.

- [x] Design decisions finalized (22 decisions, see `docs/reports/local-tts-helper-design-decisions.md`)
- [x] Readiness contract defined (see `docs/integration/zam-reader-readiness-contract.md`)
- [x] Engine research complete (see `docs/reports/local-tts-solutions-research.md`)
- [x] Architecture backbone docs (see `docs/architecture/`)
- [x] ADRs (see `docs/adr/`)
- [ ] Runtime implementation
- [ ] Engine adapters (Piper-plus, Kokoro)
- [ ] REST + WebSocket API
- [ ] CLI (`zam-tts`)
- [ ] Test suite
- [ ] Packaging (uv/pipx Phase 1)

---

## Quick start (once implemented)

```bash
# Install
uv tool install zam-local-tts-helper
# or
pipx install zam-local-tts-helper

# Check environment
zam-tts doctor

# Start server
zam-tts serve

# Pair with Zam Reader (from a second terminal)
zam-tts pair

# Install a voice model
zam-tts models install piper-plus.en-us.lessac.medium

# Speak
zam-tts speak --text "Hello from local TTS" --play
```

---

## Documentation index

| Document | What it covers |
|---|---|
| [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md) | Annotated repo + package layout |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | System design, SoC, layers, module boundaries |
| [`docs/TECH_STACK.md`](docs/TECH_STACK.md) | Packages, logging strategy, DevEX, UX patterns |
| [`docs/adr/README.md`](docs/adr/README.md) | Architecture Decision Records index |
| [`docs/integration/zam-reader-readiness-contract.md`](docs/integration/zam-reader-readiness-contract.md) | Requirements before Zam Reader may use this helper |
| [`docs/reports/local-tts-helper-design-decisions.md`](docs/reports/local-tts-helper-design-decisions.md) | Full 22-decision design log |
| [`docs/reports/local-tts-solutions-research.md`](docs/reports/local-tts-solutions-research.md) | Engine research and benchmarks |
| [`docs/zam-reader-context.md`](docs/zam-reader-context.md) | What Zam Reader is and why this helper exists |

---

## Architecture in one diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│  Zam Reader (browser extension)                                 │
│    LocalTTSProvider → LocalTTSBridge → LocalhostTransport       │
└───────────────────────────┬─────────────────────────────────────┘
                            │  /v1 REST + WebSocket (localhost only)
┌───────────────────────────▼─────────────────────────────────────┐
│  zam-local-tts-helper                                           │
│                                                                 │
│  CLI (zam-tts)          API (FastAPI + uvicorn)                 │
│    serve / pair           /v1/health, /v1/engines              │
│    doctor                 /v1/voices, /v1/catalog              │
│    engines / voices       /v1/models, /v1/storage              │
│    models / storage       /v1/diagnostics, /v1/pair            │
│    speak                  WS /v1/events                         │
│                                                                 │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐    │
│  │EngineRegistry│  │  ModelManager  │  │ CatalogManager   │    │
│  │  PiperPlus   │  │  installer     │  │  bundled catalog  │    │
│  │  Kokoro      │  │  verifier      │  │  remote refresh   │    │
│  └──────────────┘  └────────────────┘  └──────────────────┘    │
│                                                                 │
│  Security: token auth · origin allowlist · rate limits         │
│  Storage:  ~/Library/Application Support/Zam Local TTS/        │
│  Logging:  structlog · JSON in prod · console in dev           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Boundary rules (non-negotiable)

- Zam Reader **never imports** Python helper code
- Zam Reader **never sends raw filesystem paths** to the helper
- Zam Reader **never calls `fetch('http://127.0.0.1:...')`** from content/UI code directly
- The helper **never assumes** Zam Reader is the only client
- The helper **never logs raw user text** in any diagnostic or log sink
- Model installs use **`modelId` only**, never raw URLs from the client

---

## License

GPLv3 — same as Zam Reader. See `LICENSE`.
