# Rotate pairing token and recover cleanly

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0009 — `docs/adr/ADR-0009-pairing-flow.md`

## What to build

Implement token rotation through the pairing workflow so users can invalidate a compromised token and force clients to re-pair without corrupting helper config or model state.

## Acceptance criteria

- [x] `mery pair --rotate` generates a new long-lived token and invalidates the old one. E2E tests invoke the real CLI rotate command and prove the token changes while helper ID remains stable.
- [x] Existing clients with the old token receive structured `auth.invalid_token` responses. Protected REST requests now return taxonomy-shaped `auth.token_invalid` envelopes with `pair_client` guidance after CLI rotation or any invalid bearer token.
- [x] Re-pairing succeeds with a fresh one-time code and leaves helper ID/model storage intact. E2E tests rotate, create a fresh pairing code, claim it through `/v1/pair/claim`, and verify the helper ID is preserved with the rotated token.
- [x] Tests cover rotation, old-token rejection, helper restart, and successful re-pair. Contract coverage exercises CLI rotate, running-app auth reload, old-token rejection, fresh pair-code claim, and helper ID preservation.

## Blocked by

- 02-claim-pairing-code-for-long-lived-token

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Ensure token rotation updates the live daemon auth configuration or requires an explicit safe restart with clear client behavior. Live app auth checks reload the persisted token per protected request, so old tokens are invalidated without restart.
- [x] Add end-to-end tests: old token rejected, new pair code claimed, helper ID/storage preserved, existing clients receive re-pair guidance. Contract coverage proves old token rejection, new pair-code claim, helper ID preservation after CLI rotation, and `pair_client` guidance in structured invalid-token envelopes.

## Comments
