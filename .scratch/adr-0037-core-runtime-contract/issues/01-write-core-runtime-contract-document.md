# Write core runtime contract document

Status: completed

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Create the core runtime contract documentation that defines what the backend guarantees before the web console can scale. The document should describe the public runtime capabilities, ownership boundaries, test gates, and non-goals that every client consumes through `/v1`.

## Acceptance criteria

- [x] A core runtime contract document exists and is linked from the ADR or docs index.
- [x] The contract covers engines, voices, install/readiness, synthesis/fallback, streaming, diagnostics/errors, storage, and test strategy.
- [x] The contract explicitly says the console consumes runtime behavior through `/v1` and generated client types only.
- [x] The contract distinguishes fake-engine default gates from optional real-engine smoke tests.
- [x] The contract states that model training/quality competition is out of scope; Mery integrates engines/providers.

## Blocked by

None - can start immediately

## Evidence

- `docs/architecture/core-runtime-contract.md` defines the living core runtime contract and is linked from `docs/adr/ADR-0037-core-runtime-contract.md`, `docs/README.md`, and `AGENTS.md`.
- `tests/unit/test_console_runtime_contract_docs.py::test_core_runtime_contract_is_linked_and_covers_console_boundaries` pins the required headings, generated-client-only Console boundary, fake-engine/default gate language, optional real-engine smoke language, and model-training out-of-scope statement.
- Verification: `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — 31 passed.
