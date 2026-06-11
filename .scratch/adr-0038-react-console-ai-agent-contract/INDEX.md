# ADR-0038 — React Console Architecture and AI-Agent Design Contract

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## Issues

1. `issues/01-create-console-design-contract-and-index.md`
2. `issues/02-bootstrap-vite-react-typescript-console-tooling.md`
3. `issues/03-generate-and-wrap-openapi-client.md`
4. `issues/04-build-react-console-shell-auth-and-voices-tracer-bullet.md`
5. `issues/05-add-console-packaging-build-freshness-and-static-route-gates.md`
6. `issues/06-add-console-quality-gates-and-accessibility-smoke.md`
7. `issues/07-add-developer-mode-contract-for-playground-health-and-debug-surfaces.md`

## Current status

- Issues 01–07 are completed with production evidence.
- React Console source is built into packaged Python static assets under `src/mery_tts/console`.
- ADR-0038 stack evidence: Vite + React + TypeScript, TanStack Router, TanStack Query, TanStack Table, Radix-backed owned UI primitives, React Hook Form + Zod, Tailwind v4, generated OpenAPI client wrappers, dependency-cruiser, knip, Vitest/RTL/MSW, Playwright, and Axe are all on the verified path.
- Verification evidence: `pnpm build` and `pnpm console-check` passed for the packaged React console, including dependency-cruiser (`67 modules`, `106 dependencies`, no violations), knip, Playwright/Axe against `/console` served by `uv run mery serve`, and build/API freshness checks.
- Repository contract evidence: `uv run pytest tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` passed (`39 passed`) and `uv run ruff check tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` passed.
- Audit remediation evidence: governance-gated voices remain visible but no longer expose install actions; `VoicesPanel.test.tsx` covers gated install suppression while an allowed uninstalled voice still exercises the confirm/install path.

Definition of Done review:
- ADR/contract updated: yes — ADR-0038 points to `docs/console/DESIGN.md`; issue evidence now records the production stack and gates.
- fake-engine deterministic tests: N/A — Console-only frontend/package work; backend fake-engine behavior was not changed.
- API contract tests: yes — `uv run pytest tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` (`39 passed`).
- CLI or Console proof: yes — `pnpm console-check` packaged `/console` Playwright smoke.
- diagnostics/error sanitization tests: yes — Developer Mode evidence remains sanitized and contract-pinned in `tests/unit/test_console_runtime_contract_docs.py`.
- docs/help updated: yes — `docs/console/DESIGN.md`, ADR-0038 evidence, and local issue evidence.
- optional real-engine smoke: N/A — no real engine adapter/runtime dependency path changed.
- UI gates: yes — `pnpm console-check` covers Vitest/RTL/MSW, Playwright, and Axe.
- privacy gates: yes — token persistence remains explicit; Developer Mode states raw private text, bearer tokens, reference audio, and private paths stay redacted.
