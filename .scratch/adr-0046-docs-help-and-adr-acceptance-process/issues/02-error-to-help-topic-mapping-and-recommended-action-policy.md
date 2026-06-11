# Error to help topic mapping and recommended action policy

Status: needs-triage

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Attach local help topic IDs and recommended actions to user-actionable structured errors.

## Acceptance criteria

- [ ] User-actionable errors include `help_topic` or `docs_url` plus `recommended_action`.
- [ ] Console and CLI prefer local help; online docs are optional supplement.
- [ ] Error taxonomy has help topic assignments.
- [ ] Tests verify correct help references on structured errors.

## Evidence required

- [ ] Error mapping table.
- [ ] Structured error tests.
- [ ] CLI/Console help rendering proof.

## Blocked by

- 01
