# Audit log schema and security event boundaries

Status: needs-triage

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Create a bounded sanitized audit log separate from diagnostics for security-sensitive local events.

## Acceptance criteria

- [ ] Audit covers pairing, token rotation, install confirmation, direct-install grants, catalog/source changes, and security-sensitive config changes.
- [ ] Audit log is local-only, bounded, and sanitized.
- [ ] Audit never stores raw text, tokens, reference audio, or private paths.
- [ ] Diagnostics and audit have separate retention/visibility boundaries.

## Evidence required

- [ ] Audit schema tests.
- [ ] Redaction tests.
- [ ] Retention tests.
- [ ] Boundary test separating audit from diagnostics.

## Blocked by

None - can start immediately
