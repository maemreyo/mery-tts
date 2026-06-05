# Expose loaded engine runtime health status

Status: ready-for-agent

## Parent

ADR-0004 amendment — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Extend engine discovery/status behavior so import-time adapter failures remain skipped, while adapters that load successfully but fail runtime health checks are visible through `/v1/engines` as degraded or unavailable with safe status reasons.

## Acceptance criteria

- [ ] Import-time adapter load failures are logged and skipped without crashing startup.
- [ ] Loaded adapters with failed runtime checks appear in `/v1/engines` with `status: degraded` or `status: unavailable`.
- [ ] Status reasons are safe for clients and do not leak local paths, secrets, or stack traces.
- [ ] Tests cover skipped import failures, degraded loaded adapters, unavailable loaded adapters, and all-healthy adapters.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Comments
