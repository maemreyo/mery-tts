# ADR-0006 — Full localhost security model

Source ADR: `docs/adr/ADR-0006-security-model.md`

## Goal

Treat localhost as an untrusted IPC boundary by enforcing loopback-only bind, per-install token authentication, origin allowlist, rate limits, request limits, model ID hardening, and sanitized security diagnostics.

## Issues

1. [Persist secure per-install token and config](issues/01-persist-secure-per-install-token-and-config.md)
2. [Add auth origin rate and size middleware](issues/02-add-auth-origin-rate-and-size-middleware.md)
3. [Reject unsafe model IDs and sensitive diagnostics](issues/03-reject-unsafe-model-ids-and-sensitive-diagnostics.md)
