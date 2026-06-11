# Add console quality gates and accessibility smoke

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Make console quality gates enforceable from the first React slice. The completed slice provides a single check path that catches formatting, typing, architecture drift, unused dependencies, broken user flows, and accessibility regressions.

## Acceptance criteria

- [x] `console-check` runs lint, typecheck, unit/component tests, boundary checks, unused dependency/export checks, build freshness, and browser smoke.
  - Evidence: `web/console/package.json` defines `console-check` as `pnpm lint && pnpm typecheck && pnpm test && pnpm boundary && pnpm unused && pnpm check:api && pnpm check:fresh && pnpm e2e`; the latest run passed all stages.
- [x] Playwright loads the packaged `/console` route in a real browser and verifies the React Voices tracer bullet can render.
  - Evidence: `web/console/playwright.config.ts` starts `uv run mery serve`; `web/console/e2e/console-smoke.spec.ts` verifies `Mery Console`, bearer-token input, User Mode navigation, and Voices region.
- [x] Axe checks run against the packaged console and fail on serious/critical accessibility violations.
  - Evidence: `web/console/e2e/console-smoke.spec.ts` uses `@axe-core/playwright` with WCAG 2A/2AA tags and asserts no serious/critical violations.
- [x] Component tests use role/name assertions and cover keyboard-relevant interactions for forms and first-slice user flows.
  - Evidence: `web/console/src/features/voices/__tests__/VoicesPanel.test.tsx`, `AppShell.test.tsx`, `PlaygroundPanel.test.tsx`, `HealthPanel.test.tsx`, and `DeveloperPanel.test.tsx` use Testing Library role/name assertions and user-event interactions across Radix Select/Dialog/Switch, React Hook Form forms, TanStack Router mounting, and governance-gated voice install suppression.
- [x] The console gate is executable as a dedicated project check while root-project enforcement remains separately decidable.
  - Evidence: `pnpm console-check` passed end-to-end in `web/console`; ADR evidence records the transition gate without requiring Node at runtime.

## Blocked by

- Completed: `issues/05-add-console-packaging-build-freshness-and-static-route-gates.md`

## Evidence

- `pnpm console-check` — passed lint, typecheck, Vitest (`6 passed`, `8 tests`), dependency-cruiser (`67 modules`, `106 dependencies`, no violations), knip, generated API freshness, build freshness, Playwright packaged `/console` smoke, and Axe serious/critical accessibility gate.
- `uv run pytest tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — `39 passed`.
- `uv run ruff check tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — passed.
- `tests/unit/test_console_runtime_contract_docs.py::test_react_console_scaffold_has_tooling_source_and_quality_gates` pins the quality-gate files/scripts.
