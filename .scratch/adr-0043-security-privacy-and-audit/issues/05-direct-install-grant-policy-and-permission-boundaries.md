# Direct install grant policy and permission boundaries

Status: needs-triage

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Define future direct-install grants with scoped client identity, install class, time window, user confirmation, revocation, audit, and expiry.

## Acceptance criteria

- [ ] Direct installs remain disabled by default.
- [ ] Grants are scoped by client identity, install class, and time window.
- [ ] Persistent grants require permissions UI, revocation, audit trail, and expiry.
- [ ] Grant use emits audit events and respects local-only/air-gapped policy.

## Evidence required

- [ ] Grant scoping tests.
- [ ] Audit emission tests.
- [ ] Expiry/revocation tests.
- [ ] Policy enforcement tests.

## Blocked by

- 02
- 03
