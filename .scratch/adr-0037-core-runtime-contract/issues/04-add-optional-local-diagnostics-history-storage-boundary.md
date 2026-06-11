# Add optional local diagnostics history storage boundary

Status: needs-triage

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Define and, if needed, implement a repository boundary for future local diagnostics/history/settings storage. This slice should not put runtime synthesis correctness on a database; it only prepares the system for local-only observability and console history features.

## Acceptance criteria

- [ ] A storage boundary exists or is documented for diagnostics history, playground history, settings, and local-only measurements.
- [ ] The boundary can be backed by current file stores first and a future SQLite implementation later without changing API or console components.
- [ ] Runtime synthesis, voice resolution, install correctness, and readiness correctness do not depend on database availability.
- [ ] Corrupt or unavailable diagnostics-history storage degrades safely and reports a sanitized diagnostic.
- [ ] Tests prove the boundary can be faked in memory and does not affect synthesis or install flows.

## Blocked by

- `issues/01-write-core-runtime-contract-document.md`
