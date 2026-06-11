# Branch Definition of Done checklist and enforcement mechanisms

Status: needs-triage

## Parent

ADR-0046 — `docs/adr/ADR-0046-docs-help-and-adr-acceptance-process.md`

## Type

AFK

## What to build

Document production-ready branch DoD and how agents verify it before considering implementation complete.

## Acceptance criteria

- [ ] DoD covers ADR/contract updates, fake-engine deterministic tests, API contract tests, CLI/Console proof, diagnostics/error sanitization, docs/help updates, and optional real-engine smoke.
- [ ] UI branches require Vitest/RTL/MSW, Playwright, and accessibility checks.
- [ ] Privacy requirements forbid raw input text, tokens, audio, and private path logging.
- [ ] Enforcement mechanism is documented in agent or contribution guidance.

## Evidence required

- [ ] DoD document excerpt.
- [ ] Link from agent/contribution guidance.
- [ ] Checklist review evidence.

## Blocked by

None - can start immediately
