# Local help topic packaging contract and offline recovery layout

Status: completed

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Package local help topics for common recovery paths so users can recover without internet.

## Acceptance criteria

- [x] Help topics cover install/setup, pairing/token, missing optional dependency, model corrupt/reinstall, catalog invalid/signature/checksum, local-only/air-gapped, diagnostics export, unsupported format/locale, and provider unavailable.
- [x] Topics are locally accessible without internet.
- [x] Packaging contract defines topic IDs, titles, and body format.
- [x] Console/CLI can reference topic IDs.

## Evidence required

- [x] Help topic manifest.
- [x] Offline access test.
- [x] Packaging test.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/help/` packages local help topics and manifest for offline recovery.
- `src/mery_tts/errors/factories.py` and taxonomy code map structured errors to help topics, docs URLs, and recommended actions.
- `docs/agents/definition-of-done.md`, `docs/agents/adr-status-rules.md`, and `docs/agents/adr-promotion-workflow.md` define acceptance and promotion process with tests.
- `tests/unit/test_local_help.py`, `tests/cli/test_help_cli.py`, `tests/unit/test_definition_of_done_docs.py`, `tests/unit/test_adr_status_rules_docs.py`, and `tests/unit/test_adr_promotion_workflow_docs.py` cover docs/help/process behavior.
- Verification: ADR-0046 focused verification previously recorded: docs/help/process gate passed; current API/core verification remains green.
