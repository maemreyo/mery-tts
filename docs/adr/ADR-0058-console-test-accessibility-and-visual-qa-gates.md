# ADR-0058 — Console Test, Accessibility, and Visual QA Gates

**Status:** Accepted
**Date:** 2026-06-12  
**Source:** Web Console Runtime Control Plane grill — testability and UI quality decisions

## Context

The Console is user-facing UI for a local runtime. Clean TypeScript diagnostics are insufficient: regressions can occur in recovery decisions, network state handling, keyboard access, responsive layout, status announcements, and visual readability.

## Decision

Use a scoped three-layer test and QA contract for Runtime Control Plane work:

1. **Pure unit tests** for view models and decision engines, including Overview next action, voice availability, connection state, and query-key helpers.
2. **Component tests with MSW** for Overview, Connection card, Voices table/cards, Playground picker/advanced raw id, Health states, and Developer schema preview.
3. **Browser smoke and accessibility checks** for real user flows, including connection, Overview recovery, Voices install path, Playground smoke path, Health error/recovery state, and Developer opt-in preview.

Add scoped visual QA for key Console surfaces:

- Overview guided recovery/status;
- Connection card;
- Voices desktop table and mobile cards;
- Playground installed picker and advanced options;
- Health and Developer states.

Checks must cover role/name, keyboard flow, `role="status"`, `role="alert"`, focus-visible styling, contrast-sensitive states, responsive behavior, and privacy-sensitive content.

## Rationale

Pure view-model tests keep decision logic readable and fast. MSW-backed component tests verify UI behavior against stable API contracts. Browser/a11y/visual QA proves the actual user surface works beyond type checking.

## Consequences

**Enables:** AFK-ready implementation issues, safer refactors, and clear completion evidence under the branch Definition of Done.

**Constrains:** Runtime Control Plane UI work is not done until docs/ADR updates, unit/component/browser evidence, accessibility checks, and privacy review are recorded where applicable.

## Related

- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- [ADR-0046 — Docs, Help, and ADR Acceptance Process](ADR-0046-docs-help-and-adr-acceptance-process.md)
- [docs/agents/definition-of-done.md](../agents/definition-of-done.md)
- [docs/console/DESIGN.md](../console/DESIGN.md)
- Issue set: `.scratch/web-console-runtime-control-plane/`
