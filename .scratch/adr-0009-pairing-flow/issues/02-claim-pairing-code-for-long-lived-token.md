# Claim pairing code for long-lived token

Status: ready-for-agent

## Parent

ADR-0009 — `docs/adr/ADR-0009-pairing-flow.md`

## What to build

Implement `/v1/pair/claim` as the only unauthenticated endpoint, exchanging a valid one-time code for helper ID, port, long-lived auth token, contract version, and capabilities.

## Acceptance criteria

- [ ] Valid claim returns schema version, helper ID, port, auth token, contract version, and capabilities.
- [ ] Pairing code is invalidated immediately after first successful claim.
- [ ] Expired, reused, and wrong codes return structured `auth.*` errors.
- [ ] Failed claim attempts are rate-limited and logged without the code value.

## Blocked by

- 01-generate-one-time-pairing-code-and-setup-url
- ADR-0005 issue 02-implement-rest-management-endpoints

## Comments
