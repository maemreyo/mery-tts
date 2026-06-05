# Ship curated bundled catalog fixtures

Status: ready-for-agent

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Create a curated bundled catalog and tiny test fixtures that let users browse initial voices offline and let tests exercise catalog/model behavior without downloading real large models.

## Acceptance criteria

- [ ] Bundled catalog includes representative Piper-plus and Kokoro entries with normalized model IDs and engine IDs.
- [ ] Vietnamese Piper-plus metadata uses normalized locale `vi-VN` while preserving correct upstream file names and roles.
- [ ] Fixture catalog/model files support unit and contract tests without network access.
- [ ] Documentation distinguishes offline reading behavior from explicit model/catalog network actions.

## Blocked by

- 01-define-catalog-schemas-and-verifier-policy

## Comments
