# ADR-0009 — Pairing code + setup URL flow

Source ADR: `docs/adr/ADR-0009-pairing-flow.md`

## Goal

Implement deliberate user-confirmed pairing where `mery pair` creates a one-time code and setup URL, and `/v1/pair/claim` exchanges it for a long-lived helper auth token.

## Issues

1. [Generate one-time pairing code and setup URL](issues/01-generate-one-time-pairing-code-and-setup-url.md)
2. [Claim pairing code for long-lived token](issues/02-claim-pairing-code-for-long-lived-token.md)
3. [Rotate pairing token and recover cleanly](issues/03-rotate-pairing-token-and-recover-cleanly.md)
