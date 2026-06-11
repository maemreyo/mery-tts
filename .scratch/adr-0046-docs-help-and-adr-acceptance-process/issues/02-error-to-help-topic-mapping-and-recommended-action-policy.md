# Error to help topic mapping and recommended action policy

Status: completed

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Attach local help topic IDs and recommended actions to user-actionable structured errors.

## Acceptance criteria

- [x] User-actionable errors include `help_topic` or `docs_url` plus `recommended_action`.
- [x] Console and CLI prefer local help; online docs are optional supplement.
- [x] Error taxonomy has help topic assignments.
- [x] Tests verify correct help references on structured errors.

## Evidence required

- [x] Error mapping table.
- [x] Structured error tests.
- [x] CLI/Console help rendering proof.

## Blocked by

- 01

## Evidence

- `src/mery_tts/help/` packages local help topics and manifest for offline recovery.
- `src/mery_tts/errors/factories.py` and taxonomy code map structured errors to help topics, docs URLs, and recommended actions.
- `docs/agents/definition-of-done.md`, `docs/agents/adr-status-rules.md`, and `docs/agents/adr-promotion-workflow.md` define acceptance and promotion process with tests.
- `tests/unit/test_local_help.py`, `tests/cli/test_help_cli.py`, `tests/unit/test_definition_of_done_docs.py`, `tests/unit/test_adr_status_rules_docs.py`, and `tests/unit/test_adr_promotion_workflow_docs.py` cover docs/help/process behavior.
- Verification: ADR-0046 focused verification previously recorded: docs/help/process gate passed; current API/core verification remains green.
