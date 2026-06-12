# Overview landing with guided recovery and status

Status: ready-for-agent

## What to build

Add Overview as the default landing surface. It should answer “Can I use Mery right now, and what should I do next?” with one primary CTA, up to two secondary actions, and compact status evidence based only on current connection, health, and voice availability data.

## Acceptance criteria

- [ ] Overview is the default landing section in the Console navigation model.
- [ ] Overview renders a Connection card when the Console is disconnected or token is missing.
- [ ] Overview uses a pure view-model decision engine for next action, secondary actions, status tiles, and explanatory copy.
- [ ] The decision engine is covered by unit tests for happy path, no token, server unreachable, no usable voices, voices available, and degraded health.
- [ ] Overview does not display last install job or persisted smoke result in v1.
- [ ] Overview can navigate to Voices, Playground, Health, or Developer without owning those features' business logic.
- [ ] Component tests with MSW cover loading, error, empty, ready, and degraded states.
- [ ] Accessibility coverage verifies primary CTA role/name, focus order, `role="status"`, and screen-reader-visible status text.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md`
- `02-connection-module-and-query-keys.md`

## Related

- `docs/adr/ADR-0053-overview-guided-recovery-and-status.md`
- `docs/adr/ADR-0054-console-connection-module-and-shared-query-keys.md`
- `docs/console/DESIGN.md`

## Comments
