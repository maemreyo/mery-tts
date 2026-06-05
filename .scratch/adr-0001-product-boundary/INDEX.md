# ADR-0001 — Product / ownership boundary

Source ADR: `docs/adr/ADR-0001-product-boundary.md`

## Goal

Implement the standalone helper boundary so Zam Reader only integrates through a versioned `/v1` bridge contract, never through Python internals, raw paths, or raw model URLs.

## Issues

1. [Create standalone helper package boundary](issues/01-create-standalone-helper-package-boundary.md)
2. [Enforce bridge-only integration contract](issues/02-enforce-bridge-only-integration-contract.md)
