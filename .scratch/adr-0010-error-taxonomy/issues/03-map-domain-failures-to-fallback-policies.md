# Map domain failures to fallback policies

Status: completed

## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Implement the fallback-policy map that tells clients and CLI diagnostics how to respond to helper failures without relying on unstructured strings or ad-hoc per-call decisions.

## Acceptance criteria

- [ ] Connection failures map to Web Speech fallback plus setup action metadata.
- [ ] Model-missing and synthesis failures map to install/retry/fallback behavior according to ADR-0010.
- [ ] Auth and security failures map to safe no-retry or re-pair actions.
- [ ] Tests prove representative errors from every category include correct recommended action and fallback policy.

## Blocked by

- 01-define-structured-error-taxonomy

## Comments
