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

- Issues 01–07 are completed with evidence.
- React Console source is built into packaged Python static assets under `src/mery_tts/console`.
- Verification evidence: `pnpm build` and `pnpm console-check` passed for the packaged React console, including Playwright/Axe against `/console` served by `uv run mery serve`.
