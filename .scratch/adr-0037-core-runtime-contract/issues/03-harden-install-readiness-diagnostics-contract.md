# Harden install, readiness, and diagnostics contract

Status: completed

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Harden the core control-plane contract that the console will use for first-run setup, voice install, readiness, smoke status, and diagnostics. The completed slice should make the backend the source of truth for user-facing recovery and developer-facing diagnostic detail.

## Acceptance criteria

- [x] Install job responses expose durable, terminal, and pollable state that the console can render without inferring backend internals.
- [x] Readiness responses expose a clear ready/not-ready decision, usable voice counts, provider/runtime summaries, and actionable next steps.
- [x] Diagnostics responses are sanitized: no raw user text, no private filesystem paths, no secrets, and stable machine-readable codes.
- [x] Smoke status is represented as backend-owned runtime evidence, not frontend-derived state.
- [x] Contract tests cover user-mode recovery states and developer-mode diagnostic payloads without real downloads.

## Blocked by

- `issues/01-write-core-runtime-contract-document.md`

## Evidence

- `docs/architecture/core-runtime-contract.md` defines install/readiness, diagnostics/error, and storage contracts as backend-owned `/v1` behavior.
- `tests/contract/test_api_core.py` covers console-facing `/v1` auth/static route boundaries, install confirmation, storage advisory/cleanup, diagnostics/export surfaces, and user-mode recovery assertions.
- Existing diagnostics sanitization coverage remains in diagnostics/history/export tests; the contract now prevents Console from deriving these states itself.
- Verification: `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — 31 passed.
