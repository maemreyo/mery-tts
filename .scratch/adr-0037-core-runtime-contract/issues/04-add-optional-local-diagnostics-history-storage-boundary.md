# Add optional local diagnostics history storage boundary

Status: completed

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Define and, if needed, implement a repository boundary for future local diagnostics/history/settings storage. This slice should not put runtime synthesis correctness on a database; it only prepares the system for local-only observability and console history features.

## Acceptance criteria

- [x] A storage boundary exists or is documented for diagnostics history, playground history, settings, and local-only measurements.
- [x] The boundary can be backed by current file stores first and a future SQLite implementation later without changing API or console components.
- [x] Runtime synthesis, voice resolution, install correctness, and readiness correctness do not depend on database availability.
- [x] Corrupt or unavailable diagnostics-history storage degrades safely and reports a sanitized diagnostic.
- [x] Tests prove the boundary can be faked in memory and does not affect synthesis or install flows.

## Blocked by

- `issues/01-write-core-runtime-contract-document.md`

## Evidence

- `docs/architecture/core-runtime-contract.md` documents file-store-first diagnostics history/playground history/settings/local measurement boundaries and explicitly forbids runtime synthesis/install/readiness correctness from depending on a database.
- Existing diagnostics history/export tests prove bounded local storage and corrupt-history degradation; the new contract test pins the boundary as required Console guidance.
- Verification: `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — 31 passed.
