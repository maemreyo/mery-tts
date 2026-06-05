# ADR-0003 — Python-first runtime

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 7

## Context

The helper could be implemented in Rust (best perf, hardest), Node/Electron
(familiar to Zam Reader team, wrong runtime for ML), or Python (best ML ecosystem,
needs guardrails to avoid becoming "loose scripts").

## Decision

Use **Python 3.12+ as the primary runtime**, with strict typed package structure
and product-grade guardrails.

Package manager: **`uv`** (not pip, not poetry).  
Build backend: **hatchling** (PEP 517/518 compliant, fast, minimal config).

## Rationale

- Python has the strongest immediate ecosystem for Piper-plus wrappers, kokoro-onnx,
  ONNX Runtime, audio processing, FastAPI, and model management tooling.
- Development velocity matters for product validation; Rust would slow the design
  iteration loop significantly.
- `uv` is 10–100× faster than pip for installs, has lockfile support, and integrates
  cleanly with CI. It is the correct choice for a Python-first project in 2026.
- Strict guardrails — typed modules, `ruff`, `mypy --strict`, `depcruise` boundary
  checks — prevent Python from becoming a mess of loose scripts.

## Guardrails (non-negotiable)

- `src/` layout (PEP 518) — no accidental test code imports in prod
- `py.typed` marker (PEP 561) — consumers can type-check against this package
- `mypy --strict` in CI — no `Any` escapes without explicit `# type: ignore` with reason
- `ruff` lint + format — single tool, no debate on formatting style
- Engine-specific dependencies are optional extras in `pyproject.toml`
- No engine-specific branching allowed outside the engine's own adapter directory

## Consequences

**Enables:**
- Fast development iteration
- Rich ML ecosystem access
- `uv tool install` / `pipx install` as the Phase 1 distribution path

**Constrains:**
- Python startup time adds ~100–200ms to first `mery` invocation; mitigated by
  daemon mode (warm, long-running server).
- Packaging for end-users requires explicit steps (Phase 2: standalone binary;
  Phase 3: signed installer). See ADR-0008.
- The helper must work on Python 3.12+. Do not use 3.13-only features until 3.12
  EOL (2028).

## Related

- ADR-0008 (packaging strategy)
- `docs/TECH_STACK.md`
- `docs/reports/local-tts-solutions-research.md` (engine benchmark data)
