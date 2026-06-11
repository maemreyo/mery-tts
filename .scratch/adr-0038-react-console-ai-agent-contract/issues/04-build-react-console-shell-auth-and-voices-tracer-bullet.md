# Build React console shell, auth, and Voices tracer bullet

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Build the first React console vertical slice: app shell, token handling, navigation, and the Voices catalog/install lifecycle. This slice should prove the full architecture end to end without attempting to migrate Playground, Health, or Developer surfaces yet.

## Acceptance criteria

- [ ] The React shell loads at `/console` and supports User Mode navigation for the first slice.
- [ ] Token handling is centralized, memory-only by default, with an explicit remember-this-device option and logout clearing memory and storage.
- [ ] Voices catalog and installed voices load through generated-client wrappers and TanStack Query.
- [ ] Catalog table supports user-centric search/filter/sort and degrades to usable cards on small screens.
- [ ] Install starts by backend model/catalog identifier, polls job state through TanStack Query, and refreshes installed voices on terminal status.
- [ ] User-facing copy is English-only but routed through semantic i18n keys.
- [ ] Unit/component tests with MSW cover loading, empty, error, install-progress, install-success, and install-failure states.

## Blocked by

- `issues/03-generate-and-wrap-openapi-client.md`
- ADR-0037 issue `../adr-0037-core-runtime-contract/issues/03-harden-install-readiness-diagnostics-contract.md`
