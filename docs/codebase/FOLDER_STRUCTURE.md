# Folder Structure

Complete annotated layout of the `zam-local-tts-helper` repository and Python package.

---

## Repository root

```text
zam-local-tts-helper/
│
├── src/                        # Source root (PEP 518 src-layout)
│   └── zam_tts/                # Python package (importable as `zam_tts`)
│
├── tests/                      # Test suite (mirrors src/ structure)
│
├── scripts/                    # Dev/CI helper scripts (not installed)
│
├── docs/                       # All documentation
│   ├── architecture/           # System design docs
│   ├── adr/                    # Architecture Decision Records
│   ├── integration/            # Readiness contracts for external clients
│   └── reports/                # Research + decision logs (source of truth)
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # PR gate: lint + type-check + unit + contract tests
│       └── integration.yml     # Scheduled/manual: real engine + model install tests
│
├── pyproject.toml              # PEP 517/518 project config, deps, tool config
├── justfile                    # Task runner (just test, just lint, just dev, ...)
├── CHANGELOG.md                # Semantic versioning changelog
└── README.md                   # Entry point
```

---

## Python package: `src/zam_tts/`

The package follows **hexagonal architecture**: domain/core is pure Python with no
I/O; infrastructure (filesystem, network, audio, server) lives in adapters at the
edges. Every layer boundary is enforced by `depcruise` rules in CI.

```text
src/zam_tts/
│
├── __init__.py                 # Package version, public surface (minimal)
├── __main__.py                 # `python -m zam_tts` → `zam-tts serve`
├── py.typed                    # PEP 561: declares this package ships inline types
│
├── api/                        # FastAPI application + routes + WS handlers
│   ├── __init__.py
│   ├── app.py                  # create_app() factory; mounts routers + middleware
│   ├── dependencies.py         # FastAPI Depends: settings, registry, token, etc.
│   ├── middleware.py           # Auth token check, rate limit, request size guard
│   ├── routes/
│   │   ├── health.py           # GET /v1/health
│   │   ├── engines.py          # GET /v1/engines
│   │   ├── voices.py           # GET /v1/voices/installed
│   │   ├── catalog.py          # GET /v1/catalog/voices
│   │   ├── models.py           # POST /v1/models/install, GET /v1/models/install/{jobId}
│   │   │                       # DELETE /v1/models/{modelId}; delegates install side effects
│   │   │                       # to orchestrators/model_install.py
│   │   ├── storage.py          # GET /v1/storage
│   │   ├── diagnostics.py      # GET /v1/diagnostics
│   │   └── pair.py             # POST /v1/pair/claim
│   ├── orchestrators/
│   │   └── model_install.py    # Consumes ModelManager.install() AsyncIterator[InstallEvent]
│   │                           # Emits WS install.* schemas and calls VoiceRegistry.refresh()
│   │                           # after InstallDone; routes stay thin, models stay WS-agnostic
│   └── ws/
│       └── events.py           # WS /v1/events — install.progress, audio.chunk, etc.
│
├── schemas/                    # Pydantic v2 request/response models (versioned)
│   ├── __init__.py             # Re-exports v1 schemas as the current public surface
│   ├── common.py               # Shared types: ErrorCode, Severity, SchemaVersion
│   └── v1/
│       ├── __init__.py
│       ├── health.py           # HealthResponse, EngineStatus
│       ├── engines.py          # EngineDescriptor, EngineCapabilities
│       ├── voices.py           # VoiceDescriptor, InstalledVoice
│       ├── catalog.py          # CatalogVoice, CatalogResponse
│       ├── models.py           # InstallRequest, InstallJobStatus, ModelDescriptor
│       ├── events.py           # WS event union: InstallProgress, AudioChunk, etc.
│       ├── errors.py           # LocalTTSError, ErrorCategory, FallbackPolicy
│       └── pairing.py          # PairClaimRequest, PairClaimResponse
│
│   NOTE: `schemas/` was previously called `bridge_contract/` in early design
│   docs. Renamed: "bridge_contract" implied ownership of the contract; in Python
│   convention, `schemas` better describes Pydantic models. The contract is
│   defined by the readiness doc; this module just implements the data shapes.
│
├── engines/                    # TTS engine adapters (isolated, swappable)
│   ├── __init__.py
│   ├── base.py                 # EngineAdapter ABC + EngineRegistry + CancelToken
│   │                           # ABC: health(), voices(), synthesize() → AsyncIterator[PCMChunk]
│   │                           # CancelToken: shared dataclass for session cancellation
│   │                           # EngineRegistry discovers adapters via entry-points group
│   │                           # "zam_tts.engines" — open for extension, closed for modification
│   │                           # Adding a new engine = new subdirectory + one entry-point line;
│   │                           # EngineRegistry code never changes
│   ├── voice_registry.py       # VoiceRegistry — voice_id → (EngineAdapter, VoiceDescriptor)
│   │                           # SRP: EngineRegistry owns adapters; VoiceRegistry owns routing
│   │                           # Built by querying all loaded adapters; refresh() called on
│   │                           # model install/delete events (voice list may change)
│   ├── piper_plus/
│   │   ├── __init__.py
│   │   ├── adapter.py          # PiperPlusAdapter implements EngineAdapter
│   │   │                       # Owns session_id lifecycle; delegates synthesis to model_runner
│   │   └── model_runner.py     # Blocking→async bridge: ThreadPoolExecutor + asyncio.Queue
│   │                           # Uses piper_plus.PiperPlus(...) — no subprocess, no binary on PATH
│   │                           # Owns: thread pool, CancelToken registry keyed by session_id
│   └── kokoro/
│       ├── __init__.py
│       ├── adapter.py          # KokoroAdapter implements EngineAdapter
│       │                       # Owns session_id lifecycle; delegates synthesis to model_runner
│       └── model_runner.py     # Blocking→async bridge: ThreadPoolExecutor + asyncio.Queue
│                               # Uses kokoro_onnx directly — no subprocess, no binary on PATH
│                               # Owns: thread pool, CancelToken registry keyed by session_id
│
│   RULE: No engine-specific code may appear outside its own subdirectory.
│   RULE: engine adapters import from `schemas/` and `models/`; never from `api/`.
│   RULE: VoiceRegistry is the single source of truth for voice→engine routing;
│         no route handler or WS handler resolves voiceId directly.
│
├── models/                     # Model lifecycle: install, verify, delete, cache
│   ├── __init__.py
│   ├── events.py               # InstallEvent domain union: InstallProgress, InstallDone,
│   │                           # InstallFailed; standalone contract for CLI/API/tests
│   ├── manager.py              # ModelManager: install/delete/list; install() returns
│   │                           # AsyncIterator[InstallEvent] and never imports api/ or WS
│   ├── installer.py            # Download → temp → verify → atomic move
│   ├── verifier.py             # SHA256 + sizeBytes check; rolls back on failure
│   └── store.py                # Filesystem model store; path resolution by modelId
│
├── catalog/                    # Catalog: load, validate, sign, refresh
│   ├── __init__.py
│   ├── loader.py               # Load bundled or cached remote catalog
│   ├── verifier.py             # Signature + schema + expiry validation
│   ├── refresher.py            # Explicit user-triggered remote refresh
│   └── bundled/
│       └── catalog-v1.json     # Curated bundled catalog (checked into repo)
│
├── audio/                      # Audio output and PCM utilities
│   ├── __init__.py
│   ├── player.py               # CLI direct playback via sounddevice (--play mode)
│   └── encoder.py              # PCM16 → base64 chunk encoding for WS streaming
│
├── security/                   # Auth tokens, pairing, CORS, rate limiting
│   ├── __init__.py
│   ├── token.py                # Per-install token generation, rotation, validation
│   ├── pairing.py              # One-time code generation, claim, expiry
│   └── guard.py                # Rate limiter, request-size guard, path rejection
│
├── diagnostics/                # Doctor checks and structured error types
│   ├── __init__.py
│   ├── doctor.py               # DoctorCheck ABC + all runtime checks
│   └── errors.py               # LocalTTSError factory; maps codes to categories
│
├── settings/                   # App configuration and path management
│   ├── __init__.py
│   └── config.py               # HelperSettings (pydantic-settings); platformdirs paths
│
└── cli/                        # typer CLI entry points
    ├── __init__.py
    ├── main.py                 # zam-tts root app; registers sub-commands
    ├── serve.py                # zam-tts serve [--port N] [--reload]
    ├── pair.py                 # zam-tts pair
    ├── doctor.py               # zam-tts doctor
    ├── engines.py              # zam-tts engines list
    ├── voices.py               # zam-tts voices list [--engine ENGINE]
    ├── catalog.py              # zam-tts catalog list [--locale LOCALE]
    ├── models.py               # zam-tts models install|delete|list
    ├── storage.py              # zam-tts storage show|move|repair
    └── speak.py                # zam-tts speak --text TEXT [--play] [--output FILE]
```

---

## Test suite: `tests/`

Tests mirror the source tree. Every layer is tested in isolation before
integration. Engine-specific tests are marked `@pytest.mark.engine` and can be
skipped in CI if the engine binary/package is not installed.

```text
tests/
│
├── conftest.py                 # Shared fixtures: app client, fake catalog, temp dir
│
├── fixtures/
│   ├── catalog-fixture-v1.json # Tiny fixture catalog for unit/contract tests
│   └── tiny-model/             # Minimal model files for install/verify tests
│       ├── model.onnx          # 1 KB stub (real ONNX header, fake weights)
│       └── model.onnx.json     # Config stub
│
├── unit/                       # Pure logic, no I/O, no server
│   ├── test_catalog_verifier.py
│   ├── test_model_verifier.py
│   ├── test_security_token.py
│   ├── test_security_pairing.py
│   ├── test_security_guard.py
│   ├── test_diagnostics_doctor.py
│   └── test_settings_config.py
│
├── contract/                   # REST schema + WS event order tests (fake engine)
│   ├── test_rest_health.py
│   ├── test_rest_engines.py
│   ├── test_rest_voices.py
│   ├── test_rest_catalog.py
│   ├── test_rest_models.py
│   ├── test_rest_pair.py
│   ├── test_rest_diagnostics.py
│   ├── test_rest_storage.py
│   ├── test_ws_events_install.py
│   ├── test_ws_events_synthesize.py
│   └── test_rest_security.py   # missing-token, bad-token, wrong-origin, rate-limit
│
├── engine/                     # Adapter contract tests (requires engine installed)
│   ├── test_piper_plus_adapter.py  # @pytest.mark.engine("piper-plus")
│   └── test_kokoro_adapter.py      # @pytest.mark.engine("kokoro")
│
├── integration/                # Full stack: server + real or fixture engine
│   ├── test_model_install_flow.py  # install → verify → list → delete
│   └── test_synthesize_stream.py   # WS synthesize → audio.chunk* → audio.done
│
└── cli/
    ├── test_cli_doctor.py
    ├── test_cli_serve_startup.py
    ├── test_cli_pair.py
    ├── test_cli_speak_output.py    # --output to .wav (no real audio device needed)
    └── test_cli_models.py
```

---

## Scripts: `scripts/`

Dev and CI scripts not shipped with the package.

```text
scripts/
├── check_catalog_signature.py  # Verify a catalog JSON against its signature
├── gen_fixture_catalog.py      # Generate tests/fixtures/catalog-fixture-v1.json
└── check_deps.py               # Verify engine binaries/packages are available
```

---

## Docs: `docs/`

```text
docs/
│
├── README.md                   # Docs index + ownership rules
├── FOLDER_STRUCTURE.md         # This file
├── TECH_STACK.md               # Packages, logging, DevEX, UX patterns
├── zam-reader-context.md       # What Zam Reader is; why this helper exists
│
├── architecture/
│   ├── ARCHITECTURE.md         # SoC, layers, module map, data flow
│   ├── API_PROTOCOL.md         # Full REST + WebSocket contract reference
│   └── SECURITY_MODEL.md       # Token, pairing, CORS, rate limit design
│
├── adr/
│   ├── README.md               # ADR index + status table
│   ├── ADR-0001-product-boundary.md
│   ├── ADR-0002-helper-shape.md
│   ├── ADR-0003-python-runtime.md
│   ├── ADR-0004-engine-strategy.md
│   ├── ADR-0005-api-protocol.md
│   ├── ADR-0006-security-model.md
│   ├── ADR-0007-catalog-integrity.md
│   ├── ADR-0008-packaging.md
│   ├── ADR-0009-pairing-flow.md
│   └── ADR-0010-error-taxonomy.md
│
├── integration/
│   └── zam-reader-readiness-contract.md   # Acceptance gate for Zam Reader
│
└── reports/                    # Research and decision source material
    ├── local-tts-helper-design-decisions.md
    ├── local-tts-solutions-research.md
    ├── zam-reader-tts-feature-exploration.md   # copied context from zreader
    └── zam-reader-audio-grill-followup-decisions.md  # copied context from zreader
```

---

## Key layout rules

These rules are enforced by `depcruise` configuration and CI.

| Rule | Description |
|---|---|
| `api/` may import `schemas/`, `engines/`, `models/`, `catalog/`, `security/`, `diagnostics/`, `settings/` | API layer orchestrates but does not own domain logic |
| `engines/` may import `schemas/v1/`, `models/`, `settings/` only | Engine adapters are isolated from API plumbing |
| `models/` may import `schemas/v1/`, `catalog/`, `settings/` only | Model manager is independent of engine internals |
| `catalog/` may import `schemas/v1/`, `settings/` only | Catalog is a pure data/IO module |
| `security/` may import `schemas/v1/`, `settings/` only | Security has no engine or model dependency |
| `diagnostics/` may import `schemas/v1/`, `engines/`, `models/`, `security/`, `settings/` | Doctor checks read but do not write |
| `cli/` may import any module | CLI is the outermost shell; it may call anything |
| `schemas/` imports nothing from `zam_tts` | Schemas are pure Pydantic; no circular deps |
| No module imports from `tests/` or `scripts/` | Test code never leaks into production |

---

## Storage layout (runtime, macOS default)

```text
~/Library/Application Support/Zam Local TTS/
│
├── config.json                 # Port, token, allowed origins, model dir override
│
├── catalog/
│   ├── bundled-catalog.json    # Copied from package on first run
│   └── remote-catalog.json     # Cached after explicit user refresh
│
├── models/
│   ├── piper-plus/             # One subdir per engine
│   │   └── en-us.lessac.medium/
│   │       ├── model.onnx
│   │       └── model.onnx.json
│   └── kokoro/
│       └── en-us.af_heart.medium/
│           └── model.onnx
│
├── cache/
│   ├── downloads/              # In-progress download temp files
│   └── temp/                   # Atomic install staging area
│
├── logs/
│   └── helper.log              # Rotating JSON logs (structlog)
│
└── diagnostics/
    └── last-doctor.json        # Result of most recent `zam-tts doctor` run
```

Linux default: `~/.local/share/Zam Local TTS/`
Windows default: `%APPDATA%\Zam Local TTS\`

These paths are resolved at runtime by `settings/config.py` via `platformdirs`.
They are never hardcoded in tests; tests use `tmp_path` fixtures.
