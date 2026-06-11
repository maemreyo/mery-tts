# Community catalog governance lock

Status: needs-triage

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Keep community catalogs locked until signature, provenance, license, takedown, checksum, and audit requirements exist.

## Acceptance criteria

- [ ] Community catalog support remains explicitly disabled.
- [ ] Enablement requires signature validation, provenance metadata, license metadata, takedown identifiers, checksum verification, and audit trail.
- [ ] Tests/static checks prevent accidental enablement.
- [ ] Structured error explains the lock.

## Evidence required

- [ ] Lock enforcement test.
- [ ] Checklist in docs or schema comments.
- [ ] Structured error test.

## Blocked by

- 03
