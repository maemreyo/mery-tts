# Apply bundled and remote catalog trust tiers

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0007 amendment — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement the amended catalog trust policy that treats bundled catalog data as package-trusted schema-validated input and remote catalog data as untrusted network input requiring signature, freshness, schema, and allowlist validation before exposure or install.

## Acceptance criteria

- [ ] Bundled catalog loading validates schema/graph integrity without mandatory runtime signature verification.
- [ ] Remote catalog loading rejects missing/invalid signatures, expired/freshness failures, unsupported schema, and disallowed source/download hosts.
- [ ] Catalog signature verification and per-file SHA256/size verification remain separate validation layers.
- [ ] Tests cover trusted bundled load, invalid bundled schema, valid remote signature, invalid remote signature, expired remote catalog, and disallowed host.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Enforce separate trust tiers at runtime: bundled schema/graph validation, remote signature/freshness validation, and per-file install verification.
- [ ] Expose active catalog provenance so diagnostics/API can distinguish bundled, remote, stale, and rejected catalogs.

## Comments
