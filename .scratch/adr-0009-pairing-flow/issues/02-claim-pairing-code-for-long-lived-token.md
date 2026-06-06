# Claim pairing code for long-lived token

Status: production-ready
## Parent

ADR-0009 — `docs/adr/ADR-0009-pairing-flow.md`

## What to build

Implement `/v1/pair/claim` as the only unauthenticated endpoint, exchanging a valid one-time code for helper ID, port, long-lived auth token, contract version, and capabilities.

## Acceptance criteria

- [x] Valid claim returns schema version, helper ID, port, auth token, contract version, and capabilities.
- [x] Pairing code is invalidated immediately after first successful claim.
- [x] Expired, reused, and wrong codes return structured `auth.*` errors.
- [x] Failed claim attempts are rate-limited and logged without the code value.

## Blocked by

- 01-generate-one-time-pairing-code-and-setup-url
- ADR-0005 issue 02-implement-rest-management-endpoints

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Add rate limiting for failed pair claims and return stable structured `auth.*` errors for expired, reused, wrong, and throttled codes.
- [x] Prove a real CLI-created challenge can be claimed through HTTP once, then fails on reuse. Contract tests invoke `mery pair`, claim the persisted code via `/v1/pair/claim`, and verify reuse returns 401.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Add rate limiting for failed pair claims and return stable structured `auth.*` errors for expired, reused, wrong, and throttled codes.
- Prove a real CLI-created challenge can be claimed through HTTP once, then fails on reuse. Contract tests invoke `mery pair`, claim the persisted code via `/v1/pair/claim`, and verify reuse returns 401.
