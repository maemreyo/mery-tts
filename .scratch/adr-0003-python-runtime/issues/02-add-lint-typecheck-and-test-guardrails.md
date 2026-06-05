# Add lint typecheck and test guardrails

Status: ready-for-agent

## Parent

ADR-0003 — `docs/adr/ADR-0003-python-runtime.md`

## What to build

Add the strict Python quality gates that prevent the helper from becoming loose scripts: ruff lint/format, `mypy --strict`, pytest layout, and task-runner commands.

## Acceptance criteria

- [ ] Ruff lint and format checks are configured for source and tests.
- [ ] `mypy --strict` runs against `src/mery_tts`.
- [ ] Pytest has unit/contract/engine/integration/CLI marker conventions.
- [ ] Local task commands run lint, typecheck, tests, and a combined check gate.

## Blocked by

- 01-configure-typed-python-packaging-with-uv-and-hatchling

## Comments
