# Harden install, readiness, and diagnostics contract

Status: needs-triage

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Harden the core control-plane contract that the console will use for first-run setup, voice install, readiness, smoke status, and diagnostics. The completed slice should make the backend the source of truth for user-facing recovery and developer-facing diagnostic detail.

## Acceptance criteria

- [ ] Install job responses expose durable, terminal, and pollable state that the console can render without inferring backend internals.
- [ ] Readiness responses expose a clear ready/not-ready decision, usable voice counts, provider/runtime summaries, and actionable next steps.
- [ ] Diagnostics responses are sanitized: no raw user text, no private filesystem paths, no secrets, and stable machine-readable codes.
- [ ] Smoke status is represented as backend-owned runtime evidence, not frontend-derived state.
- [ ] Contract tests cover user-mode recovery states and developer-mode diagnostic payloads without real downloads.

## Blocked by

- `issues/01-write-core-runtime-contract-document.md`
