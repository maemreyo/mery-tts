# Runtime control-plane API wrapper and generated-client freshness gate

Status: ready-for-agent

## What to build

Establish the Console control-plane API boundary so feature UI consumes typed feature wrappers and never raw generated endpoint functions or `fetch` directly. This slice makes the existing same-origin `/v1` contract safer to reuse across Overview, Connection, Voices, Playground, Health, and Developer.

## Acceptance criteria

- [ ] Feature components do not import generated endpoint functions directly.
- [ ] Shared/feature API wrappers expose the currently supported Console capabilities: health, voices, install start/poll, and speech smoke.
- [ ] Generated-client freshness is checked by an existing or new focused command and documented in the Console check path.
- [ ] Dependency-boundary coverage prevents generated API code from importing app code and prevents feature UI from bypassing wrappers.
- [ ] Tests prove wrapper behavior with deterministic fake/MSW-backed data.
- [ ] No raw bearer token, raw input text, reference audio, or private filesystem path is captured in test snapshots or error output.

## Blocked by

None - can start immediately.

## Related

- `docs/adr/ADR-0052-web-console-runtime-control-plane.md`
- `docs/adr/ADR-0038-react-console-ai-agent-contract.md`
- `docs/console/DESIGN.md`

## Comments
