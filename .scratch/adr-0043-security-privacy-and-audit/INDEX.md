# ADR-0043 implementation issue set

Status: completed

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Summary

Deepens security/privacy into console auth boundary, local-only enforcement, audit, remote providers, and direct install grants.

## Issues

| # | Issue | Type | Blocked by |
|---|---|---|---|
| 01 | [Console untrusted client boundary and auth enforcement](issues/01-console-untrusted-client-boundary-and-auth-enforcement.md) | AFK | None |
| 02 | [Local-only and air-gapped policy enforcement](issues/02-local-only-and-air-gapped-policy-enforcement.md) | AFK | None |
| 03 | [Audit log schema and security event boundaries](issues/03-audit-log-schema-and-security-event-boundaries.md) | AFK | None |
| 04 | [Remote provider opt-in config and audit metadata tests](issues/04-remote-provider-opt-in-config-and-audit-metadata-tests.md) | AFK | 02 |
| 05 | [Direct install grant policy and permission boundaries](issues/05-direct-install-grant-policy-and-permission-boundaries.md) | AFK | 02, 03 |
