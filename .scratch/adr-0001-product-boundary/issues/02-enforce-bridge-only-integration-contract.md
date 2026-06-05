# Enforce bridge-only integration contract

Status: ready-for-agent

## Parent

ADR-0001 — `docs/adr/ADR-0001-product-boundary.md`

## What to build

Define contract-level guardrails that keep client coupling limited to versioned schemas, stable IDs, structured errors, and sanitized diagnostics. The helper must reject raw filesystem paths and raw model URLs from client-controlled requests.

## Acceptance criteria

- [ ] Public request schemas use stable IDs such as `modelId`, `engineId`, `voiceId`, and contract version fields rather than paths or URLs.
- [ ] Validation rejects raw filesystem paths, path traversal, and raw model download URLs in client-facing fields.
- [ ] Contract tests cover accepted ID-only requests and rejected path/URL requests.
- [ ] No helper module assumes Zam Reader is the only client.

## Blocked by

- 01-create-standalone-helper-package-boundary

## Comments
