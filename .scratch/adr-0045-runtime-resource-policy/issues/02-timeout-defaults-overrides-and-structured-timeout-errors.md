# Timeout defaults overrides and structured timeout errors

Status: needs-triage

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Implement global, per-provider, and request-level timeout policy with cleanup and structured timeout errors.

## Acceptance criteria

- [ ] Global default and per-provider override exist.
- [ ] Normal clients can request shorter timeout but cannot extend indefinitely.
- [ ] Admin/config can raise limits.
- [ ] Timeout triggers cancellation/cleanup and structured error.

## Evidence required

- [ ] Timeout override tests.
- [ ] Request lower-bound tests.
- [ ] Cleanup tests.
- [ ] Structured timeout error tests.

## Blocked by

- 01
