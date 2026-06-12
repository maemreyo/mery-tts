# Health diagnostics-ready status view

Status: ready-for-agent

## What to build

Keep the v1 UI label “Health” while organizing the feature as diagnostics-ready. The view should explain live/readiness/usable voice status in plain language, reuse shared query/cache state, and provide recovery links without pretending to be a full diagnostics history surface.

## Acceptance criteria

- [ ] Health consumes shared health query state and does not duplicate polling logic unnecessarily.
- [ ] Health distinguishes token missing, checking, unreachable, ready, not ready, and degraded states.
- [ ] Recovery guidance is action-oriented and can link users to Overview, Voices, Playground, or Developer where appropriate.
- [ ] Health v1 does not claim live diagnostics history or log inspection unless backed by an existing `/v1` contract.
- [ ] Error content avoids raw tokens, raw input text, reference audio, and private paths.
- [ ] Component tests with MSW cover no token, loading, ready, not ready, unreachable, and degraded states.
- [ ] Accessibility checks cover status semantics, focusable recovery actions, and contrast-sensitive text.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md`
- `02-connection-module-and-query-keys.md`

## Related

- `docs/adr/ADR-0057-diagnostics-ready-health-and-developer-schema-preview.md`
- `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`
- `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Comments
