# Add console packaging, build freshness, and static-route gates

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Connect the React build output to the Python package boundary and add checks proving packaged static assets are fresh, present, and served correctly without a Node.js runtime.

## Acceptance criteria

- [x] The console build emits static assets into `src/mery_tts/console` in the package-resource shape served by FastAPI.
  - Evidence: `web/console/vite.config.ts` sets `outDir: "../../src/mery_tts/console"` and `base: "/console/"`; `pnpm build` emitted `src/mery_tts/console/index.html` plus hashed Vite JS/CSS under `src/mery_tts/console/assets/`.
- [x] Built assets are committed and a check fails when packaged output is missing or references stale asset paths.
  - Evidence: `web/console/scripts/check-build-fresh.mjs` verifies packaged index references `/console/assets/*.js` and `/console/assets/*.css`, and verifies those referenced hashed assets exist.
- [x] Python tests verify `/console`, `/console/setup`, `/console/assets/*`, and SPA fallback continue to work.
  - Evidence: `tests/contract/test_api_core.py::test_console_static_routes_are_public_spa_without_affecting_v1_auth`.
- [x] Package-resource shape is preserved for console assets.
  - Evidence: `src/mery_tts/console/__init__.py`, `src/mery_tts/console/index.html`, and `src/mery_tts/console/assets/*` remain package resources consumed by FastAPI static route code.
- [x] Asset serving handles Vite-emitted JavaScript and CSS safely.
  - Evidence: `pnpm console-check` runs `check:fresh` and Playwright loads packaged `/console` through `uv run mery serve`, proving the hashed Vite JS/CSS resolve from `/console/assets/`.
- [x] Running the Python server and loading `/console` does not require Node.js.
  - Evidence: Playwright e2e starts `uv run mery serve` via `web/console/playwright.config.ts` and loads the already-built packaged React output.

## Blocked by

- Completed: `issues/04-build-react-console-shell-auth-and-voices-tracer-bullet.md`

## Evidence

- `pnpm build` — emitted packaged React assets into `src/mery_tts/console/index.html` plus hashed `/console/assets/index-Dt6ysx-f.js` and `/console/assets/index-AkCkVfli.css`.
- `pnpm console-check` — passed generated API freshness, build freshness, and real-browser packaged `/console` smoke through Python server.
- `uv run pytest tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — `39 passed`, including `/console`, `/console/setup`, `/console/assets/*`, SPA fallback, and package-resource route contracts.
- `uv run ruff check tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — passed.
