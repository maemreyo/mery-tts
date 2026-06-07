# Tech Stack

Package choices, logging strategy, developer experience (DevEX), and UX patterns
for `mery-tts-server`.

---

## Package decisions

### Runtime dependencies

| Package | Version | Why |
|---|---|---|
| `fastapi` | `≥0.115` | Modern async Python web framework; Pydantic v2 native; OpenAPI docs auto-generated |
| `uvicorn[standard]` | `≥0.30` | ASGI server with uvloop + httptools for performance |
| `pydantic` | `v2, ≥2.9` | Schema validation, serialization, strict types; v2 is significantly faster than v1 |
| `pydantic-settings` | `≥2.6` | Settings from env vars + config files with type safety |
| `typer` | `≥0.13` | Type-safe CLI built on Click; integrates with Rich for output |
| `rich` | `≥13` | Tables, progress bars, colored output, panels in CLI |
| `structlog` | `≥24.4` | Structured logging with context binding; JSON in prod, dev-friendly console in dev |
| `httpx` | `≥0.27` | Async HTTP client for catalog downloads; supports streaming + timeouts |
| `platformdirs` | `≥4.3` | OS-correct app data paths (`~/Library/...`, `~/.local/share/...`, `%APPDATA%`) |
| `sounddevice` | `≥0.4` | Cross-platform audio playback for `--play` CLI mode |
| `soundfile` | `≥0.12` | Read/write WAV/AIFF for `--output` CLI mode |
| `numpy` | `≥1.26` | PCM buffer handling; required by both sounddevice and ONNX engines |
| `anyio` | `≥4.6` | Async primitives (cancel scopes, task groups) used by uvicorn/FastAPI |
| `cryptography` | `≥43` | Ed25519 signature verification for remote catalog; `secrets` module handles auth tokens |

### Engine optional dependencies (installed per-user need)

```toml
[project.optional-dependencies]
piper-plus = ["piper-plus[inference]>=1.0"]
kokoro     = ["kokoro-onnx>=0.4"]
all        = ["mery-tts-server[piper-plus,kokoro]"]
```

**Why `piper-plus` over original `piper-tts`:**

| Attribute | `piper-plus` | `piper-tts` (original) |
|---|---|---|
| License | **MIT** | GPL-3.0 |
| espeak-ng dep | **None** | Required (GPL transitive) |
| Archived | No (active) | Yes (archived Oct 2025) |
| EN model size | **38 MB** | 60 MB |
| Latency (P50) | **27 ms** | 35 ms |
| Vietnamese | Yes (`vi_VM_meeting`) | Yes (community) |

**Why `kokoro-onnx` for Kokoro:**
- Pure ONNX Runtime backend — no PyTorch, no CUDA requirement
- CPU-first: works on any machine, including M2 without GPU
- Smaller memory footprint than the full kokoro-tts-tool (350 MB model)
- API is simple enough to wrap cleanly in `KokoroAdapter`

### Development dependencies

```toml
[project.optional-dependencies]
dev = [
  "ruff>=0.7",
  "mypy>=1.13",
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "pytest-httpx>=0.32",
  "respx>=0.21",
  "coverage[toml]>=7.6",
  "types-soundfile",
]
```

| Package | Why |
|---|---|
| `ruff` | Single tool: lint + format (replaces black + isort + flake8). Extremely fast. |
| `mypy` | Static type checker; `strict = true` is the target |
| `pytest` | Standard test framework |
| `pytest-asyncio` | `asyncio_mode = "auto"` — all async tests work without `@pytest.mark.asyncio` |
| `pytest-httpx` | Mock `httpx` calls for catalog download tests |
| `respx` | HTTP mock router for more complex catalog/download scenarios |
| `coverage[toml]` | Coverage with `pyproject.toml` config; HTML + LCOV reports |

---

## `pyproject.toml` skeleton

```toml
[project]
name = "mery-tts-server"
version = "0.1.0"
description = "Standalone local TTS helper for Zam Reader"
license = { text = "GPL-3.0-or-later" }
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.9",
  "pydantic-settings>=2.6",
  "typer>=0.13",
  "rich>=13",
  "structlog>=24.4",
  "httpx>=0.27",
  "platformdirs>=4.3",
  "sounddevice>=0.4",
  "soundfile>=0.12",
  "numpy>=1.26",
  "anyio>=4.6",
  "cryptography>=43",
]

[project.scripts]
mery = "mery_tts.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mery_tts"]

[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM", "ANN", "S", "RUF"]
ignore = ["ANN101", "ANN102"]
per-file-ignores = { "tests/**" = ["S101", "ANN"] }

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
strict = true
python_version = "3.12"
files = ["src/mery_tts"]
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
  "engine: marks tests that require an actual engine binary/package (skip with -m 'not engine')",
  "integration: marks tests that start a real server and may download fixture models",
]

[tool.coverage.run]
source = ["mery_tts"]
branch = true
omit = ["src/mery_tts/__main__.py"]

[tool.coverage.report]
exclude_lines = [
  "pragma: no cover",
  "if TYPE_CHECKING:",
  "@abstractmethod",
]
```

---

## Logging strategy

### Philosophy

- **Structured JSON in production** — every log line is a machine-readable JSON object
- **Human-friendly in development** — Rich-formatted, colored, indented
- **No user text, ever** — synthesized text, article content, and page URLs must never appear in any log line
- **Context binding** — request ID, session ID, and engine ID are bound to the log context before any handler runs

### Structlog setup

```python
# mery_tts/settings/logging.py

import logging
import sys
import structlog

def configure_logging(*, dev: bool = False) -> None:
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if dev:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=processors,
        )
    else:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=processors,
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

### Log context binding pattern

```python
# In API middleware — bind request ID early, carry through all handlers
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

async def request_context_middleware(request: Request, call_next):
    clear_contextvars()
    bind_contextvars(
        request_id=request.headers.get("X-Request-Id", generate_request_id()),
        path=request.url.path,
        method=request.method,
    )
    response = await call_next(request)
    return response
```

### Logging rules

| What to log | How |
|---|---|
| Server startup / shutdown | `INFO` — port, version, engine statuses |
| Incoming REST requests | `INFO` — method, path, request_id; no query params with user data |
| Auth failures | `WARNING` — reason code, origin, no token value |
| Rate limit hits | `WARNING` — endpoint, origin, no user data |
| Engine health checks | `INFO` — engine_id, status |
| Model install progress | `INFO` — job_id, model_id, percent; no URLs with tokens |
| Model verify success | `INFO` — model_id, sha256 prefix (first 8 chars) |
| Model verify failure | `ERROR` — model_id, expected vs actual sha256 |
| Synthesis start/end | `DEBUG` — session_id, engine_id, voice_id, char_count |
| Synthesis errors | `ERROR` — session_id, error_code; NO text content |
| Doctor checks | `INFO` — check_name, status, detail |

**Never log:**
- Synthesized text or article content
- Selected vocabulary
- Page URL or article URL
- Auth token values (only the presence/absence)
- User identifiers
- Raw file paths provided by clients

### Log file rotation

```python
# File handler for production (in addition to stdout)
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    settings.log_path / "helper.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8",
)
```

---

## Developer experience (DevEX)

### Task runner: `justfile`

```makefile
# justfile

# List all tasks
default:
    just --list

# Install all deps (including dev + all engines)
install:
    uv sync --all-extras

# Start dev server with hot reload
dev:
    uv run uvicorn mery_tts.api.app:create_app --reload --port 8765 --factory

# Run all tests (skip engine tests that need binaries)
test:
    uv run pytest -m "not engine and not integration" -v

# Run full test suite including engine + integration
test-all:
    uv run pytest -v

# Lint + format check
lint:
    uv run ruff check src/ tests/
    uv run ruff format --check src/ tests/

# Auto-fix lint issues
fix:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Type check
typecheck:
    uv run mypy src/mery_tts

# Coverage report
coverage:
    uv run pytest -m "not engine and not integration" --cov=mery_tts --cov-report=html --cov-report=term-missing

# Full gate: lint + typecheck + tests
check:
    just lint
    just typecheck
    just test

# CLI: run doctor
doctor:
    uv run mery doctor

# CLI: start server (no reload)
serve:
    uv run mery serve

# CLI: pair
pair:
    uv run mery pair

# Generate fixture catalog
fixtures:
    uv run python scripts/gen_fixture_catalog.py
```

**Why `just` over `make`:**
- No tab vs. space ambiguity
- No implicit rules inherited from make
- Recipes are clearly named and self-documenting
- Works identically on macOS, Linux, and Windows (via `just --shell powershell.exe` on Windows)

### VS Code recommended setup

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "always"
    }
  },
  "mypy-type-checker.preferDaemon": true
}
```

Recommended extensions: `charliermarsh.ruff`, `ms-python.mypy-type-checker`,
`ms-python.python`, `tamasfe.even-better-toml`.

### First-run setup (for new contributors)

```bash
git clone https://github.com/maemreyo/mery-tts
cd mery-tts

# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all deps including engines  ← REQUIRED before running anything
# Entry-points (EngineRegistry discovery) are only registered after this step.
just install

# Verify environment
just doctor

# Run tests (no engine required — tests inject FakeEngineAdapter directly)
just test

# Start dev server
just dev
```

The `just install` command runs `uv sync --all-extras`. The `.venv` is created
automatically by `uv` in the project root. No manual `pip install` needed.

### Environment variables for development

```bash
# .env (gitignored)
MERY_TTS_ENV=development          # Enables console logging, hot reload hints
MERY_TTS_PORT=8765                # Default: 8765. On conflict: structured error, no silent fallback
MERY_TTS_LOG_LEVEL=DEBUG          # Verbose logs
MERY_TTS_DATA_DIR=/tmp/mery   # Isolated data dir for dev (avoids clobbering real data)
```

`pydantic-settings` reads these automatically. No extra config files needed.

---

## UX patterns

### CLI output with Rich

All `mery` commands use Rich for output. Consistent patterns:

```python
# mery doctor output
from rich.console import Console
from rich.table import Table

console = Console()

def print_doctor_results(checks: list[DoctorCheck]) -> None:
    table = Table(title="Doctor Results", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="dim")
    table.add_column("Status")
    table.add_column("Detail")
    for check in checks:
        status = "[green]✓ OK[/]" if check.ok else "[red]✗ FAIL[/]"
        table.add_row(check.name, status, check.detail or "")
    console.print(table)
```

```python
# mery models install — progress bar
from rich.progress import Progress, DownloadColumn, BarColumn, TimeRemainingColumn

with Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    DownloadColumn(),
    TimeRemainingColumn(),
) as progress:
    task = progress.add_task(f"Downloading {model_id}", total=total_bytes)
    async for chunk in download_stream:
        progress.update(task, advance=len(chunk))
```

### CLI error output

All errors are printed to stderr; exit code 1 on failure.

```python
# mery_tts/cli/utils.py
import sys
import typer

def fatal(msg: str, error: LocalTTSError | None = None) -> None:
    typer.echo(f"[red]Error:[/] {msg}", err=True, color=True)
    if error:
        typer.echo(f"  Code: {error.code}", err=True)
        typer.echo(f"  Action: {error.recommended_action}", err=True)
    raise typer.Exit(code=1)
```

### Server startup output

```text
  Mery TTS Server  v0.1.0
  ──────────────────────────────
  Status    healthy
  Engines   piper-plus ✓  kokoro ✓
  Port      8765
  Paired    yes (1 client)
  Logs      ~/Library/Application Support/Mery TTS/logs/helper.log

  Press Ctrl+C to stop.
```

This is printed once on startup via `uvicorn.config.LOGGING_CONFIG`-override, then
the server switches to structured log output only.

### OpenAPI / Swagger UI

FastAPI auto-generates OpenAPI docs at `http://127.0.0.1:8765/docs` in dev mode.
The API is also machine-readable at `http://127.0.0.1:8765/openapi.json` for use
in Zam Reader contract test generation.

In production (non-dev env), the docs endpoint is disabled:
```python
app = FastAPI(
    title="Mery TTS Server",
    docs_url="/docs" if settings.env == "development" else None,
    redoc_url=None,
)
```

### WS event stream debugging

In development, the `/v1/events` WebSocket can be inspected with:

```bash
# Using websocat (brew install websocat)
websocat "ws://127.0.0.1:8765/v1/events" \
  -H "Authorization: Bearer $(cat ~/.config/mery/token)"
```

All events include `schemaVersion`, `requestId`, and `timestamp` for correlation.

---

## CI strategy

```yaml
# .github/workflows/ci.yml — runs on every PR

name: CI
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --extra dev
      - run: just lint
      - run: just typecheck
      - run: just test          # skips engine + integration tests
      - run: just coverage
      - uses: codecov/codecov-action@v4
```

```yaml
# .github/workflows/integration.yml — runs nightly or on tag

name: Integration
on:
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  integration:
    runs-on: macos-latest      # Must match real deployment target (macOS/ARM)
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --all-extras   # installs piper-plus + kokoro
      - run: just test-all          # includes engine + integration tests
```

**Why two workflows:** Normal CI is fast (< 2 min) and never downloads model files.
Integration CI runs on macOS (real target hardware) with actual engine binaries.
Heavy model downloads are gated behind explicit test marks; they do not run on PRs.
