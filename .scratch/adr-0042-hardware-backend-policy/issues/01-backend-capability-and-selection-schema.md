# Backend capability and selection schema

Status: needs-triage

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Represent supported backends, selected backend, fallback reason, and missing optional extras with global default plus per-provider override.

## Acceptance criteria

- [ ] Schema includes supported candidates, selected backend, fallback reason, and missing extras.
- [ ] Global default and per-provider override are supported.
- [ ] No per-voice backend complexity is introduced.
- [ ] Serialization is additive and backward-compatible.

## Evidence required

- [ ] Schema excerpt.
- [ ] Serialization tests.
- [ ] Config fixture tests.

## Blocked by

None - can start immediately
