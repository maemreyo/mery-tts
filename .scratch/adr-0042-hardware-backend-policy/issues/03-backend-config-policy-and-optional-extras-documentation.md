# Backend config policy and optional extras documentation

Status: needs-triage

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Document base package, provider extras, backend extras, and network/privacy constraints for runtime dependencies.

## Acceptance criteria

- [ ] Missing extras degrade gracefully instead of crashing.
- [ ] `local_only` and `air_gapped` policies are respected.
- [ ] No auto-download of runtime dependencies occurs.
- [ ] Docs explain install commands or package extras.

## Evidence required

- [ ] Docs excerpt.
- [ ] Missing extras tests.
- [ ] Network/no-auto-download assertion.

## Blocked by

- 01
