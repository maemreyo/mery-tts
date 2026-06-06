# Ship curated bundled catalog fixtures

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Create a curated bundled catalog and tiny test fixtures that let users browse initial voices offline and let tests exercise catalog/model behavior without downloading real large models.

## Acceptance criteria

- [x] Bundled catalog includes representative Piper-plus and Kokoro entries with normalized model IDs and engine IDs.
- [x] Vietnamese Piper-plus metadata uses normalized locale `vi-VN` while preserving correct upstream file names and roles.
- [x] Fixture catalog/model files support unit and contract tests without network access.
- [x] Documentation distinguishes offline reading behavior from explicit model/catalog network actions. README Phase 1 copy states the bundled catalog is package data that can be browsed offline, while explicit model installation and remote catalog refresh are separate user-triggered network actions; `tests/unit/test_doctor_storage_packaging_rollout.py::test_readme_documents_phase_one_uv_and_pipx` pins this distinction.

## Blocked by

- 01-define-catalog-schemas-and-verifier-policy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Load bundled catalog fixtures as package data at runtime and expose voice cards through `/v1/catalog/voices`.
- [x] Ensure fixtures represent installable Kokoro/Piper-plus runtime shapes, not only schema examples.

## Comments
