# Streaming disconnect cancellation and first-byte fallback rules

Status: needs-triage

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Handle client disconnects, resource release, and phase-aware fallback: fallback before first byte only, structured termination after first byte.

## Acceptance criteria

- [ ] Client disconnect cancels synthesis and releases resources.
- [ ] Diagnostics include `cancelled_by=client_disconnect`.
- [ ] Fallback is allowed only before first byte.
- [ ] After first byte, stream ends with structured failure/cancellation diagnostics.

## Evidence required

- [ ] Streaming route disconnect tests.
- [ ] Fallback state-machine tests.
- [ ] Resource release tests.
- [ ] Diagnostics tests.

## Blocked by

- 01
- 02
