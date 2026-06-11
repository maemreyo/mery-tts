# Generate and wrap OpenAPI client

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Add generated TypeScript API types/client from the FastAPI OpenAPI schema and wrap it in feature-level API modules. The completed slice should make the frontend consume backend contracts without raw endpoint strings or duplicated backend logic in components.

## Acceptance criteria

- [ ] The console has a repeatable OpenAPI generation command that outputs committed generated code under a quarantined directory.
- [ ] Generated code is never hand-edited and is verified fresh by a check command.
- [ ] Feature API wrappers expose the operations needed by the first Voices tracer bullet.
- [ ] UI components consume feature hooks/view-models rather than raw fetch or generated endpoint functions.
- [ ] Tests can use MSW handlers aligned with the generated contracts.

## Blocked by

- `issues/02-bootstrap-vite-react-typescript-console-tooling.md`
- ADR-0037 issue `../adr-0037-core-runtime-contract/issues/02-add-runtime-contract-api-and-fake-engine-gates.md`
