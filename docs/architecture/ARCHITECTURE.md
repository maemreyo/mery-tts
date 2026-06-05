# Architecture

`zam-local-tts-helper` is a **standalone Python application** with a strict layered
architecture. It is designed to be: **SoC-clean, modular, standalone, scalable, and
adaptive** — meaning it works independently of Zam Reader, supports multiple engines
without coupling, runs on CPU/GPU/ANE hardware, and can be packaged in multiple ways
without changing its internal structure.

---

## Design principles

| Principle | What it means here |
|---|---|
| **Separation of Concerns** | Each module has one explicit job. API routes do not own domain logic. Engines do not own storage. Security does not know about engines. |
| **Hexagonal / Ports & Adapters** | Domain core (engine adapters, model manager, catalog, diagnostics) has no dependency on FastAPI, CLI, or filesystem paths. Infrastructure adapters (API, CLI, audio, storage) live at the edges. |
| **Modular engines** | Each TTS engine is a self-contained adapter behind a common `EngineAdapter` ABC. Adding a new engine means adding one subdirectory under `engines/`; nothing else changes. |
| **Standalone** | The helper is fully testable and usable without Zam Reader. `zam-tts speak --play` works with no extension present. Contract tests run against a fake engine with no model download. |
| **Scalable** | New engines, voices, locales, and catalog sources can be added without modifying existing code. `EngineRegistry` and `ModelManager` are open for extension, closed for modification. |
| **Adaptive** | The transport layer (localhost HTTP now, Native Messaging later) is behind an abstraction. The packaging method (uv, standalone binary, signed installer) does not affect internal structure. The hardware backend (CPU/ANE/GPU) is chosen by the engine adapter, invisible to callers. |

---

## Layer map

```text
┌────────────────────────────────────────────────────────┐
│  Layer 0 — Entry Points                                │
│  cli/            (typer commands: zam-tts serve, ...)  │
│  api/app.py      (FastAPI app factory)                 │
│  __main__.py     (python -m zam_tts)                   │
└──────────────────────────┬─────────────────────────────┘
                           │  calls
┌──────────────────────────▼─────────────────────────────┐
│  Layer 1 — API / Transport                             │
│  api/routes/     (REST endpoints under /v1)            │
│  api/ws/         (WebSocket /v1/events)                │
│  api/middleware/ (auth check, rate limit, size guard)  │
│  schemas/v1/     (Pydantic request/response models)    │
└──────────────────────────┬─────────────────────────────┘
                           │  delegates to
┌──────────────────────────▼─────────────────────────────┐
│  Layer 2 — Domain / Core                               │
│  engines/        (EngineRegistry, EngineAdapter ABC)   │
│  models/         (ModelManager, installer, verifier)   │
│  catalog/        (CatalogManager, loader, verifier)    │
│  security/       (token, pairing, guard)               │
│  diagnostics/    (DoctorCheck, LocalTTSError)          │
│  settings/       (HelperSettings, path resolution)     │
└──────────────────────────┬─────────────────────────────┘
                           │  uses
┌──────────────────────────▼─────────────────────────────┐
│  Layer 3 — Infrastructure / Adapters                   │
│  engines/piper_plus/   (PiperPlusAdapter)              │
│  engines/kokoro/       (KokoroAdapter)                 │
│  audio/player.py       (sounddevice CLI playback)      │
│  audio/encoder.py      (PCM16 → base64 WS chunks)     │
│  models/store.py       (filesystem model store)        │
│  catalog/bundled/      (catalog-v1.json)               │
└────────────────────────────────────────────────────────┘
```

---

## Module dependency graph (allowed → arrows)

```text
cli/       → api/, engines/, models/, catalog/, security/, diagnostics/, settings/, schemas/
api/       → engines/, models/, catalog/, security/, diagnostics/, settings/, schemas/
engines/   → schemas/v1/, models/, settings/
models/    → schemas/v1/, catalog/, settings/
catalog/   → schemas/v1/, settings/
security/  → schemas/v1/, settings/
diagnostics/ → schemas/v1/, engines/, models/, security/, settings/
schemas/   → (nothing inside zam_tts)
settings/  → (nothing inside zam_tts)
audio/     → settings/
```

**Strict prohibitions:**

- `engines/` never imports `api/` — engines do not know the server exists
- `models/` never imports `engines/` — model storage is engine-agnostic
- `catalog/` never imports `engines/` or `models/` — catalog is pure data
- `schemas/` never imports anything from `zam_tts` — no circular deps
- No module imports from `tests/` or `scripts/`

---

## Engine adapter contract

All TTS engines implement the same ABC. The API layer and CLI speak only to this
interface; they never know whether they are using Piper-plus or Kokoro.

```python
# engines/base.py (simplified)
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from zam_tts.schemas.v1 import EngineDescriptor, PCMChunk, VoiceDescriptor

class EngineAdapter(ABC):

    @property
    @abstractmethod
    def engine_id(self) -> str: ...

    @abstractmethod
    async def health(self) -> EngineStatus: ...

    @abstractmethod
    async def voices(self) -> list[VoiceDescriptor]: ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        session_id: str,
    ) -> AsyncIterator[PCMChunk]: ...

    @abstractmethod
    async def cancel(self, session_id: str) -> None: ...
```

`EngineRegistry` is a simple container that holds registered adapters, checks
their health at startup, and returns descriptors without exposing internals.

---

## Data flow: synthesize request (extension mode)

```text
Zam Reader
  LocalTTSBridge.synthesize(text, voiceId, sessionId)
  → POST /v1/events (WS, already connected)
    sends: { type: "synthesize.request", sessionId, voiceId, text }

API ws/events.py
  → authenticate request (token in WS handshake header)
  → resolve voiceId → engineId via VoiceRegistry
  → call EngineRegistry.get(engineId).synthesize(text, voiceId, sessionId)
  → async for chunk in adapter.synthesize(...):
      emit audio.chunk event with base64 PCM16 payload
  → emit audio.done event

Zam Reader
  → buffers chunks, decodes PCM16
  → plays via Web Audio / offscreen document
  → emits PlaybackEvent.utteranceStarted / wordBoundary / done
```

---

## Data flow: model install

```text
Zam Reader
  → POST /v1/models/install  { modelId: "piper-plus.en-us.lessac.medium" }
  ← { jobId: "...", status: "queued" }

API routes/models.py
  → ModelManager.start_install(modelId)
    → CatalogManager.resolve(modelId)         # get URL, sha256, sizeBytes
    → security: verify URL against allowlist
    → download to cache/temp/  via httpx streaming
    → ModelVerifier.verify(file, sha256, size)
      → on fail: delete temp, emit install.failed
    → atomic move to models/piper-plus/en-us.lessac.medium/
    → update model store index

WS /v1/events emits:
  install.progress { jobId, bytesDownloaded, totalBytes, percent }
  ...
  install.done { jobId, modelId }
  # or
  install.failed { jobId, error: LocalTTSError }
```

---

## Localhost security model (summary)

Full design in `docs/architecture/SECURITY_MODEL.md` and ADR-0006.

```text
Network
  bind only 127.0.0.1 / ::1
  never bind 0.0.0.0

Authentication
  per-install token in config.json
  every REST request: Authorization: Bearer <token>
  every WS connection: token in Sec-WebSocket-Protocol header

CORS / Origin
  allowlist of configured extension origins
  no wildcard *
  reject unknown origins

Request hardening
  request body: ≤ 100 KB
  text input: ≤ 10 000 chars
  rate limits: 60 req/min synthesize, 10 req/min install
  model IDs only — no raw filesystem paths from client

Pairing
  one-time code, 10-minute TTL
  POST /v1/pair/claim exchanges code → long-lived token
  code invalidated after first valid claim
```

---

## Cross-platform and packaging adaptability

The helper is **packaging-agnostic**. The same code runs in:

| Mode | How it is launched | Notes |
|---|---|---|
| `uv tool install` / `pipx` | `zam-tts serve` in terminal | Phase 1 default |
| Standalone binary (PyInstaller/Nuitka) | Double-click or CLI path | Phase 2 |
| Signed `.pkg` / `.dmg` | macOS installer with launchd | Phase 3 (optional) |

The `settings/config.py` module resolves OS-correct app data paths via `platformdirs`
at runtime. No path is hardcoded; no packaging method changes the internal behavior.

Engine adapter dependencies are **optional extras** in `pyproject.toml`:

```toml
[project.optional-dependencies]
piper-plus = ["piper-plus[inference]>=1.0"]
kokoro     = ["kokoro-onnx>=0.4"]
all        = ["zam-local-tts-helper[piper-plus,kokoro]"]
```

This means the helper core can be installed without any engine. Engines are pulled
in per-user need. `zam-tts doctor` reports which engines are available.

---

## Adaptive hardware path

Each engine adapter selects its compute backend transparently:

| Engine | CPU | Apple ANE / CoreML | CUDA GPU |
|---|---|---|---|
| Piper-plus | ✅ Default (ONNX Runtime) | Planned (CoreML EP) | Possible (CUDA EP) |
| Kokoro | ✅ Default (kokoro-onnx CPU) | Planned | Possible |

The API surface, schemas, and WS events are identical regardless of hardware.
Zam Reader never knows which backend is active.

---

## Test architecture

Tests are layered to match the code layers. Each layer tests only what it owns.

```text
tests/unit/        → pure logic, no I/O, no server, no engine binary
tests/contract/    → REST + WS shape tests against TestClient (fake engine)
tests/engine/      → adapter contract tests (requires engine installed, CI-optional)
tests/integration/ → full server + real fixture model + WS event ordering
tests/cli/         → CLI command output + exit codes
```

The fake engine fixture in `conftest.py` implements `EngineAdapter` with a hard-coded
PCM sine wave. All contract tests use it. No model download ever happens in unit or
contract tests.

See `docs/TECH_STACK.md` for testing tools and CI strategy.
