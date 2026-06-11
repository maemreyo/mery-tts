# Branch Definition of Done checklist and enforcement mechanisms

Status: completed

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Document production-ready branch DoD and how agents verify it before considering implementation complete.

## Acceptance criteria

- [x] DoD covers ADR/contract updates, fake-engine deterministic tests, API contract tests, CLI/Console proof, diagnostics/error sanitization, docs/help updates, and optional real-engine smoke.
- [x] UI branches require Vitest/RTL/MSW, Playwright, and accessibility checks.
- [x] Privacy requirements forbid raw input text, tokens, audio, and private path logging.
- [x] Enforcement mechanism is documented in agent or contribution guidance.

## Evidence required

- [x] DoD document excerpt.
- [x] Link from agent/contribution guidance.
- [x] Checklist review evidence.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/help/` packages local help topics and manifest for offline recovery.
- `src/mery_tts/errors/factories.py` and taxonomy code map structured errors to help topics, docs URLs, and recommended actions.
- `docs/agents/definition-of-done.md`, `docs/agents/adr-status-rules.md`, and `docs/agents/adr-promotion-workflow.md` define acceptance and promotion process with tests.
- `tests/unit/test_local_help.py`, `tests/cli/test_help_cli.py`, `tests/unit/test_definition_of_done_docs.py`, `tests/unit/test_adr_status_rules_docs.py`, and `tests/unit/test_adr_promotion_workflow_docs.py` cover docs/help/process behavior.
- Verification: ADR-0046 focused verification previously recorded: docs/help/process gate passed; current API/core verification remains green.
