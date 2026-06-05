# Rotate pairing token and recover cleanly

Status: ready-for-agent

## Parent

ADR-0009 — `docs/adr/ADR-0009-pairing-flow.md`

## What to build

Implement token rotation through the pairing workflow so users can invalidate a compromised token and force clients to re-pair without corrupting helper config or model state.

## Acceptance criteria

- [ ] `mery pair --rotate` generates a new long-lived token and invalidates the old one.
- [ ] Existing clients with the old token receive structured `auth.invalid_token` responses.
- [ ] Re-pairing succeeds with a fresh one-time code and leaves helper ID/model storage intact.
- [ ] Tests cover rotation, old-token rejection, helper restart, and successful re-pair.

## Blocked by

- 02-claim-pairing-code-for-long-lived-token

## Comments
