# Bootstrap Vite React TypeScript console tooling

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Create the `web/console` frontend workspace with production-ready tooling and dependency governance, but without migrating the entire console UI yet. The completed slice should prove contributors can install, develop, lint, typecheck, test, and build the console consistently.

## Acceptance criteria

- [ ] `web/console` uses Vite, React, TypeScript, pnpm, and a committed lockfile.
- [ ] The workspace includes Biome, TypeScript `tsc --noEmit`, Vitest, Testing Library, MSW, Playwright, dependency-cruiser, knip, and axe tooling.
- [ ] Root project commands delegate to focused console commands such as build, test, lint, typecheck, boundary, unused, e2e, and check.
- [ ] The toolchain enforces feature-sliced import boundaries and quarantines generated API code.
- [ ] No Node.js runtime is required to run the packaged Python server; Node is build/test-time only.

## Blocked by

- `issues/01-create-console-design-contract-and-index.md`
