# Add console quality gates and accessibility smoke

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Make console quality gates enforceable from the first React slice. The completed slice should provide a single check path that catches formatting, typing, architecture drift, unused dependencies, broken user flows, and accessibility regressions.

## Acceptance criteria

- [ ] `console-check` or equivalent runs format/lint, typecheck, unit/component tests, boundary checks, unused dependency/export checks, build freshness, and browser smoke.
- [ ] Playwright loads the packaged `/console` route in a real browser and verifies the Voices tracer bullet can render against a fake/test backend surface.
- [ ] Axe checks run against key setup/auth/voices states and fail on serious accessibility violations.
- [ ] Component tests use role/name assertions and cover keyboard-relevant interactions for forms, dialogs, tables, and errors in the first slice.
- [ ] The full project check either includes console gates immediately or documents the transition point for making them mandatory.

## Blocked by

- `issues/05-add-console-packaging-build-freshness-and-static-route-gates.md`
