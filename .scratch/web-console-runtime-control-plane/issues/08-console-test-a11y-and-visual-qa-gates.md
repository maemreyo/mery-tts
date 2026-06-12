# Console test, accessibility, and visual QA gate integration

Status: ready-for-agent

## What to build

Integrate the Console Runtime Control Plane quality gates so implementation branches produce deterministic evidence for unit behavior, component behavior, browser flows, accessibility, visual QA, build/package freshness, and privacy review.

## Acceptance criteria

- [ ] Console check path covers formatting/lint, TypeScript, unit/component tests, MSW-backed states, dependency boundaries, generated API freshness, build freshness, packaged route smoke, browser smoke, and axe accessibility checks where available.
- [ ] Pure unit tests cover Overview decision engine, connection state, voice availability derivation, and query-key helpers.
- [ ] Component tests cover Overview, Connection card, Voices table/cards, Playground picker/advanced raw id, Health states, and Developer schema preview.
- [ ] Browser smoke covers connection to local Mery with fake/MSW-backed data, Overview next action, Voices navigation, Playground navigation, and Developer opt-in preview.
- [ ] Scoped visual QA evidence is captured for Overview, Connection card, Voices desktop/mobile, Playground, Health, and Developer surfaces.
- [ ] Accessibility checks cover role/name, keyboard flow, focus-visible styling, `role="status"`, `role="alert"`, contrast-sensitive states, and responsive behavior.
- [ ] Privacy review explicitly confirms no raw input text, bearer tokens, auth headers, reference audio, private paths, or private URLs appear in UI, logs, snapshots, or visual artifacts.

## Blocked by

- `03-overview-guided-recovery-and-status.md`
- `04-voices-table-cards-and-install-recovery.md`
- `05-health-diagnostics-ready-status-view.md`
- `06-playground-installed-picker-and-advanced-raw-id.md`
- `07-developer-schema-preview.md`

## Related

- `docs/adr/ADR-0058-console-test-accessibility-and-visual-qa-gates.md`
- `docs/agents/definition-of-done.md`
- `docs/console/DESIGN.md`

## Comments
