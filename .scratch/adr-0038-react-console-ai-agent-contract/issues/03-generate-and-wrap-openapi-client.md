# Generate and wrap OpenAPI client

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Add generated TypeScript API types/client from the FastAPI OpenAPI schema and wrap it in feature-level API modules. The completed slice should make the frontend consume backend contracts without raw endpoint strings or duplicated backend logic in components.

## Acceptance criteria

- [x] The console has a repeatable OpenAPI generation command that outputs committed generated code under a quarantined directory.
- [x] Generated code is never hand-edited and is verified fresh by a check command.
- [x] Feature API wrappers expose the operations needed by the first Voices tracer bullet.
- [x] UI components consume feature hooks/view-models rather than raw fetch or generated endpoint functions.
- [x] Tests can use MSW handlers aligned with the generated contracts.

## Blocked by

- `issues/02-bootstrap-vite-react-typescript-console-tooling.md`
- ADR-0037 issue `../adr-0037-core-runtime-contract/issues/02-add-runtime-contract-api-and-fake-engine-gates.md`

## Evidence

- `web/console/scripts/generate-openapi-client.mjs` writes the committed generated client under `web/console/src/api/generated/client.ts`.
- `web/console/scripts/check-generated-api-fresh.mjs` verifies required generated-client contract snippets.
- `web/console/src/shared/api/meryApi.ts` wraps the generated client for feature code.
- `web/console/src/features/voices/voicesApi.ts` exposes Voices view models without importing generated code directly.
- `tests/unit/test_console_runtime_contract_docs.py::test_react_console_components_do_not_bypass_api_wrappers` pins that feature sources do not call `fetch` or import `@api/generated` directly.
- Verification: `pnpm check:api && node scripts/check-build-fresh.mjs` passed.
