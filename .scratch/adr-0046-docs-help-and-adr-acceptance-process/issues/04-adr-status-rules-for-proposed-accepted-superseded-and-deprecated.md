# ADR status rules for Proposed Accepted Superseded and Deprecated

Status: completed

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Define ADR status semantics and how agents treat binding versus plan-to-check decisions.

## Acceptance criteria

- [x] Proposed means needs review/grill/issue set before implementation.
- [x] Accepted means binding after review, open questions resolved, issue set exists, related docs linked, and no conflicts.
- [x] Superseded and Deprecated semantics are documented.
- [x] Agent guidance treats Accepted as binding law and Proposed as plan-to-check.

## Evidence required

- [x] Status rules doc excerpt.
- [x] ADR index/process reference.
- [x] Agent guidance link.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/help/` packages local help topics and manifest for offline recovery.
- `src/mery_tts/errors/factories.py` and taxonomy code map structured errors to help topics, docs URLs, and recommended actions.
- `docs/agents/definition-of-done.md`, `docs/agents/adr-status-rules.md`, and `docs/agents/adr-promotion-workflow.md` define acceptance and promotion process with tests.
- `tests/unit/test_local_help.py`, `tests/cli/test_help_cli.py`, `tests/unit/test_definition_of_done_docs.py`, `tests/unit/test_adr_status_rules_docs.py`, and `tests/unit/test_adr_promotion_workflow_docs.py` cover docs/help/process behavior.
- Verification: ADR-0046 focused verification previously recorded: docs/help/process gate passed; current API/core verification remains green.
