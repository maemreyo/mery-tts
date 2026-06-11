# Doctor guidance for missing backend extras

Status: needs-triage

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Add doctor output for backend state, selected backend, fallback reason, missing extras, and recovery guidance.

## Acceptance criteria

- [ ] Doctor reports CPU-only, accelerated, missing-extra, and degraded states.
- [ ] Guidance tells users what to install or configure.
- [ ] Structured diagnostics align with backend schema.
- [ ] Doctor does not require remote network access.

## Evidence required

- [ ] Doctor command tests for each state.
- [ ] Snapshot or structured output evidence.
- [ ] Network-off test.

## Blocked by

- 03
