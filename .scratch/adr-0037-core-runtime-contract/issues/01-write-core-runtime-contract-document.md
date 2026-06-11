# Write core runtime contract document

Status: needs-triage

## Parent

ADR-0037 — `docs/adr/ADR-0037-core-runtime-contract.md`

## What to build

Create the core runtime contract documentation that defines what the backend guarantees before the web console can scale. The document should describe the public runtime capabilities, ownership boundaries, test gates, and non-goals that every client consumes through `/v1`.

## Acceptance criteria

- [ ] A core runtime contract document exists and is linked from the ADR or docs index.
- [ ] The contract covers engines, voices, install/readiness, synthesis/fallback, streaming, diagnostics/errors, storage, and test strategy.
- [ ] The contract explicitly says the console consumes runtime behavior through `/v1` and generated client types only.
- [ ] The contract distinguishes fake-engine default gates from optional real-engine smoke tests.
- [ ] The contract states that model training/quality competition is out of scope; Mery integrates engines/providers.

## Blocked by

None - can start immediately
