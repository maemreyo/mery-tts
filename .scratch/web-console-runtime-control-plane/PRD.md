# Web Console Runtime Control Plane PRD

Status: ready-for-agent

## Problem

Mery Console currently exposes several useful controls — token session, Voices, Playground, Health, and Developer schema preview — but the experience is still feature-first. Users must infer whether Mery is usable, what is blocking readiness, and which action should come next.

## Goal

Evolve the React Console into a production-ready local runtime control plane that is user-centric, modular, standalone, well-tested, and adapted to existing `/v1` capabilities.

## In scope

- Overview landing with guided recovery plus compact status evidence.
- Connection-first UX for local Mery token connection.
- Shared React Query keys and same-origin generated-client wrappers.
- Voices modular split with desktop table and mobile cards.
- Playground installed voice picker with collapsed advanced raw model id fallback.
- Health as a diagnostics-ready view while keeping the v1 label honest.
- Developer schema preview, clearly labeled as non-live v1 content.
- Unit, MSW component, browser smoke, accessibility, visual QA, and privacy gates.

## Out of scope for v1

- Job Center or durable install-job history.
- Last install job on Overview.
- Persisted smoke result on Overview.
- Live diagnostics inspector.
- User-configurable server URL/base path.
- Multi-user account model, OAuth, cloud sync, marketplace/storefront, provider tuning, voice cloning/reference upload, and raw PCM browser streaming.

## Related ADRs

- `docs/adr/ADR-0052-web-console-runtime-control-plane.md`
- `docs/adr/ADR-0053-overview-guided-recovery-and-status.md`
- `docs/adr/ADR-0054-console-connection-module-and-shared-query-keys.md`
- `docs/adr/ADR-0055-responsive-voices-table-and-card-presentation.md`
- `docs/adr/ADR-0056-playground-installed-picker-and-raw-id-override.md`
- `docs/adr/ADR-0057-diagnostics-ready-health-and-developer-schema-preview.md`
- `docs/adr/ADR-0058-console-test-accessibility-and-visual-qa-gates.md`

## Implementation issues

Feature work (ordered by dependency):
- `issues/01-runtime-control-plane-api-wrapper-and-freshness.md`
- `issues/02-connection-module-and-query-keys.md`
- `issues/03-overview-guided-recovery-and-status.md`
- `issues/04-voices-table-cards-and-install-recovery.md`
- `issues/05-health-diagnostics-ready-status-view.md`
- `issues/06-playground-installed-picker-and-advanced-raw-id.md`
- `issues/07-developer-schema-preview.md`
- `issues/08-console-test-a11y-and-visual-qa-gates.md`

Infrastructure (can run in parallel with or before feature work):
- `issues/09-msw-vitest-setup-and-shared-test-utilities.md`
- `issues/10-navigation-model-add-overview-section.md`
- `issues/11-topbar-compact-status-and-reconnect.md`
- `issues/12-per-panel-error-boundaries.md`
- `issues/13-dependency-cleanup-remove-unused-packages.md`

## Definition of Done review

- ADR/contract updated: yes — ADR-0052 through ADR-0058 proposed and indexed.
- fake-engine deterministic tests: N/A for docs/issues creation; required by implementation issues when runtime behavior changes.
- API contract tests: N/A for docs/issues creation; required by implementation issues when `/v1` wrappers or generated contracts change.
- CLI or Console proof: N/A for docs/issues creation; required by implementation issues for user-facing Console behavior.
- diagnostics/error sanitization tests: N/A for docs/issues creation; required by Developer/Health implementation slices.
- docs/help updated: yes — this PRD and ADRs define the implementation plan.
- optional real-engine smoke: N/A — no engine/runtime code changed.
- UI gates: N/A for docs/issues creation; required by issue 08 and relevant UI issues.
- privacy gates: yes — plan explicitly forbids raw text, bearer tokens, reference audio, private paths, and fake live diagnostics.
