# Bootstrap Vite React TypeScript console tooling

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Create the `web/console` frontend workspace with production-ready tooling and dependency governance, but without migrating the entire console UI yet. The completed slice should prove contributors can install, develop, lint, typecheck, test, and build the console consistently.

## Acceptance criteria

- [x] `web/console` uses Vite, React, TypeScript, pnpm, and a committed lockfile.
- [x] The workspace includes Biome, TypeScript `tsc --noEmit`, Vitest, Testing Library, MSW, Playwright, dependency-cruiser, knip, and axe tooling.
- [x] Root project commands delegate to focused console commands such as build, test, lint, typecheck, boundary, unused, e2e, and check.
- [x] The toolchain enforces feature-sliced import boundaries and quarantines generated API code.
- [x] No Node.js runtime is required to run the packaged Python server; Node is build/test-time only.

## Blocked by

- `issues/01-create-console-design-contract-and-index.md`

## Evidence

- `web/console/package.json`, `pnpm-lock.yaml`, `tsconfig.json`, `vite.config.ts`, `vitest.config.ts`, `biome.json`, `.dependency-cruiser.cjs`, and `knip.json` define the build/test/tooling workspace.
- `package.json` exposes `build`, `test`, `lint`, `typecheck`, `boundary`, `unused`, `e2e`, `a11y`, `generate:api`, `check:api`, `check:fresh`, and `console-check` scripts.
- `tests/unit/test_console_runtime_contract_docs.py::test_react_console_scaffold_has_tooling_source_and_quality_gates` pins the scaffold/tooling files.
- Verification: `pnpm check:api && node scripts/check-build-fresh.mjs` passed without requiring Node.js at Python server runtime. Vitest/TS LSP were blocked by missing `node_modules`/TypeScript in this environment.
