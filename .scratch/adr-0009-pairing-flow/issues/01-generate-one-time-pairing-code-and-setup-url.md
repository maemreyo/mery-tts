# Generate one-time pairing code and setup URL

Status: ready-for-agent

## Parent

ADR-0009 — `docs/adr/ADR-0009-pairing-flow.md`

## What to build

Implement `zam-tts pair` so the helper generates a short-lived one-time pairing code and prints a clear setup URL and user instructions for Zam Reader Options.

## Acceptance criteria

- [ ] Pairing codes use cryptographically secure randomness and are 6-8 alphanumeric characters.
- [ ] Codes expire after 10 minutes and are not logged in diagnostics.
- [ ] CLI output includes code, setup URL, expiry, and Zam Reader Options instructions.
- [ ] Tests cover code creation, expiry metadata, and no code leakage in logs.

## Blocked by

- ADR-0002 issue 01-create-cli-entrypoint-and-command-skeleton
- ADR-0006 issue 01-persist-secure-per-install-token-and-config

## Comments
