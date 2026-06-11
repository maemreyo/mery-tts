# Console untrusted client boundary and auth enforcement

Status: needs-triage

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Ensure the console uses `/v1` like any other browser client and all sensitive actions require token/scope checks.

## Acceptance criteria

- [ ] Console requests are treated as normal client requests.
- [ ] Important actions require token/scope.
- [ ] `/console/setup` remains public only for validated setup handoff.
- [ ] No privileged console-only endpoints exist without explicit auth/scope.

## Evidence required

- [ ] Security/API tests for console-origin requests.
- [ ] Scope enforcement tests.
- [ ] Endpoint inventory check.

## Blocked by

None - can start immediately
