# Mery TTS Server — task runner
# Usage: just <task>    (install: https://github.com/casey/just)

# Show all available tasks
default:
    @just --list --unsorted

# ─── Setup ──────────────────────────────────────────────────────────────────

# Install all deps (core + dev + all engines). REQUIRED before running anything.
# Entry-points (EngineRegistry discovery) are only registered after this step.
# Skipping this = no engines found. Run `just doctor` to verify.
install:
    uv sync --all-extras

# Install core + dev only (no engine binaries). Entry-points still registered;
# engine adapters will be skipped at load time (ImportError → WARNING, not crash).
install-dev:
    uv sync --extra dev

# ─── Development ────────────────────────────────────────────────────────────

# Start dev server with hot reload (port 8765, dev env)
dev:
    MERY_TTS_ENV=development \
    MERY_TTS_PORT=8765 \
    MERY_TTS_LOG_LEVEL=DEBUG \
    uv run uvicorn mery_tts.api.app:create_app \
      --reload \
      --port 8765 \
      --factory \
      --log-level debug

# Start server in production mode
serve:
    uv run mery serve

# Run doctor checks
doctor:
    uv run mery doctor

# Pair with Zam Reader
pair:
    uv run mery pair

# Quick speak test (requires piper-plus model installed)
speak text="Hello from Zam local TTS":
    uv run mery speak --text "{{text}}" --play

# Open OpenAPI docs in browser (dev server must be running)
docs:
    open http://127.0.0.1:8765/docs

# ─── Testing ────────────────────────────────────────────────────────────────

# Run fast tests (no engine, no integration — suitable for pre-commit)
test:
    uv run pytest -m "not engine and not integration" -v

# Run all tests including engine adapters and integration
test-all:
    uv run pytest -v

# Run only unit tests
test-unit:
    uv run pytest tests/unit/ -v

# Run only contract tests (REST + WS schema)
test-contract:
    uv run pytest tests/contract/ -v

# Run only CLI tests
test-cli:
    uv run pytest tests/cli/ -v

# Run engine adapter tests (requires piper-plus + kokoro installed)
test-engine:
    uv run pytest tests/engine/ -m engine -v

# Run integration tests (starts real server, may download tiny fixture models)
test-integration:
    uv run pytest tests/integration/ -m integration -v

# ─── Quality ────────────────────────────────────────────────────────────────

# Lint (check only)
lint:
    uv run ruff check src/ tests/

# Format check
fmt-check:
    uv run ruff format --check src/ tests/

# Auto-fix lint + format
fix:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Type check
typecheck:
    uv run mypy src/mery_tts

# Full quality gate: lint + format + typecheck + tests
check:
    just lint
    just fmt-check
    just typecheck
    just test

# Coverage report (HTML + terminal)
coverage:
    uv run pytest -m "not engine and not integration" \
      --cov=mery_tts \
      --cov-report=html \
      --cov-report=term-missing \
      -q
    @echo "\nHTML report: htmlcov/index.html"

# ─── Fixtures & Scripts ─────────────────────────────────────────────────────

# Regenerate test fixture catalog
fixtures:
    uv run python scripts/gen_fixture_catalog.py

# Verify a catalog file signature
check-catalog path="tests/fixtures/catalog-fixture-v1.json":
    uv run python scripts/check_catalog_signature.py "{{path}}"

# Check which engine binaries/packages are available
check-deps:
    uv run python scripts/check_deps.py

# ─── Package ────────────────────────────────────────────────────────────────

# Build the wheel
build:
    uv build

# Publish to PyPI (requires UV_PUBLISH_TOKEN)
publish:
    uv publish

# Clean build artifacts
clean:
    rm -rf dist/ htmlcov/ .coverage .pytest_cache/ __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
