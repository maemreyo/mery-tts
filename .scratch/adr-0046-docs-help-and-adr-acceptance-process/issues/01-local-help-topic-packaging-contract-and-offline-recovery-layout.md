# Local help topic packaging contract and offline recovery layout

Status: needs-triage

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Package local help topics for common recovery paths so users can recover without internet.

## Acceptance criteria

- [ ] Help topics cover install/setup, pairing/token, missing optional dependency, model corrupt/reinstall, catalog invalid/signature/checksum, local-only/air-gapped, diagnostics export, unsupported format/locale, and provider unavailable.
- [ ] Topics are locally accessible without internet.
- [ ] Packaging contract defines topic IDs, titles, and body format.
- [ ] Console/CLI can reference topic IDs.

## Evidence required

- [ ] Help topic manifest.
- [ ] Offline access test.
- [ ] Packaging test.

## Blocked by

None - can start immediately
