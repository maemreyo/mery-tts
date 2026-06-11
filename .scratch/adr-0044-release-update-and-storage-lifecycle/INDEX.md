# ADR-0044 implementation issue set

Status: needs-triage

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Summary

Deepens release/storage into versioning, rollback, explicit updates, storage measurement, and safe cleanup.

## Issues

| # | Issue | Type | Blocked by |
|---|---|---|---|
| 01 | [Layered versioning schema and API compatibility contract tests](issues/01-layered-versioning-schema-and-api-compatibility-contract-tests.md) | AFK | None |
| 02 | [Catalog version pinning rollback and model reinstall policy](issues/02-catalog-version-pinning-rollback-and-model-reinstall-policy.md) | AFK | 01 |
| 03 | [Explicit update confirmation and integrity policy](issues/03-explicit-update-confirmation-and-integrity-policy.md) | AFK | 01 |
| 04 | [Storage measurement and advisory UI](issues/04-storage-measurement-and-advisory-ui.md) | AFK | None |
| 05 | [Storage cleanup actions with safe model protection](issues/05-storage-cleanup-actions-with-safe-model-protection.md) | AFK | 04 |
