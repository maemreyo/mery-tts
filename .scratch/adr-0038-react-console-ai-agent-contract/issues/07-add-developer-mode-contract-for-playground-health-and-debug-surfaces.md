# Add Developer Mode contract for Playground, Health, and debug surfaces

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Define and implement the next console contract after the Voices tracer bullet: User Mode surfaces for Playground and Health, plus Developer Mode surfaces for API payloads, headers, schemas, streaming metadata, and diagnostics. This slice should expand the console without weakening the core-first boundary.

## Acceptance criteria

- [ ] Playground uses backend speech APIs and generated-client wrappers; it does not duplicate synthesis, fallback, or streaming rules.
- [ ] Health renders readiness, diagnostics, smoke status, and actionable recovery from backend-owned responses.
- [ ] Developer Mode is opt-in and reveals raw payloads, response headers, schema/examples, and debug metadata without exposing secrets or raw private text.
- [ ] Pull-based diagnostics are implemented before live event streams; live streams remain a later progressive enhancement unless separately approved.
- [ ] Tests cover User Mode and Developer Mode states with MSW and at least one real-browser flow.

## Blocked by

- `issues/06-add-console-quality-gates-and-accessibility-smoke.md`
- ADR-0037 issue `../adr-0037-core-runtime-contract/issues/03-harden-install-readiness-diagnostics-contract.md`
