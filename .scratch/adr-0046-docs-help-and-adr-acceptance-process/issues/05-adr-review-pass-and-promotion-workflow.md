# ADR review pass and promotion workflow

Status: completed

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Define a repeatable workflow for reviewing Proposed ADRs and promoting them when ready.

## Acceptance criteria

- [x] Workflow checks grill/review completion, blocking questions, issue set existence, related docs links, and conflicts with earlier ADRs.
- [x] Existing Proposed ADRs can be flagged for review pass.
- [x] Promotion updates ADR status/index consistently.
- [x] Workflow identifies when human review is required.

## Evidence required

- [x] Promotion workflow doc excerpt.
- [x] Review checklist.
- [x] Example status/index update procedure.

## Blocked by

- 04

## Evidence

- `src/mery_tts/help/` packages local help topics and manifest for offline recovery.
- `src/mery_tts/errors/factories.py` and taxonomy code map structured errors to help topics, docs URLs, and recommended actions.
- `docs/agents/definition-of-done.md`, `docs/agents/adr-status-rules.md`, and `docs/agents/adr-promotion-workflow.md` define acceptance and promotion process with tests.
- `tests/unit/test_local_help.py`, `tests/cli/test_help_cli.py`, `tests/unit/test_definition_of_done_docs.py`, `tests/unit/test_adr_status_rules_docs.py`, and `tests/unit/test_adr_promotion_workflow_docs.py` cover docs/help/process behavior.
- Verification: ADR-0046 focused verification previously recorded: docs/help/process gate passed; current API/core verification remains green.
