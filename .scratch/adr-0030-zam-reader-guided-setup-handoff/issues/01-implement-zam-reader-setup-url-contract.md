# Implement Zam Reader setup URL contract

Status: planned

## Parent

ADR-0030 — `docs/adr/ADR-0030-zam-reader-guided-setup-handoff.md`

## What to build

Implement the setup URL contract Zam Reader can open when Mery is unavailable or degraded, carrying client identity and setup intent into Mery Console safely.

## Acceptance criteria

- [ ] Mery accepts `/console/setup?client=zam-reader&intent=...` and validates known intent values.
- [ ] Unknown or malformed setup parameters produce safe fallback UI, not raw errors.
- [ ] Setup URL parsing does not grant install privileges or bypass pairing/auth rules.
- [ ] Setup UI can be opened independently of Zam Reader after initial handoff.

## Production-ready criteria

- [ ] Tests cover valid Zam Reader URL, missing client, unknown client, unknown intent, unsafe redirect value, and unauthenticated access policy.
- [ ] Docs show the canonical setup URL shape and supported intent values.
- [ ] Client identity is logged only in sanitized form.

## Blocked by

- ADR-0026 issue 01-define-setup-intent-contract
