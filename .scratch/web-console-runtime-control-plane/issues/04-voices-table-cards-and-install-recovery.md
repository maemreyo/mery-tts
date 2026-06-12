# Voices table/cards and install-state recovery

Status: ready-for-agent

## What to build

Refactor Voices into a modular feature with shared voice view models, focused data/mutation hooks, desktop table presentation, mobile card presentation, install confirmation, install polling, and recoverable status/error states.

## Acceptance criteria

- [ ] Voices data orchestration, filtering, sorting, install mutation, and install polling are separated from presentation components.
- [ ] Desktop view remains table-first and shows voice name, engine/provider, locale, governance/risk metadata, install state, and action.
- [ ] Mobile view renders cards with the same semantic information and actions without duplicating business logic.
- [ ] Install job state remains local to Voices v1 and does not leak into Overview as durable job history.
- [ ] Empty, loading, error, no token, no voices, install queued/running/succeeded/failed/cancelled states are represented with user-facing recovery copy.
- [ ] MSW-backed component tests cover table and card behavior, filtering/sorting, install confirmation, polling stop on terminal states, and catalog invalidation.
- [ ] Accessibility tests verify table headers/card labels, confirmation dialog focus behavior, status announcements, and keyboard-install path.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md`
- `02-connection-module-and-query-keys.md`

## Related

- `docs/adr/ADR-0055-responsive-voices-table-and-card-presentation.md`
- `docs/adr/ADR-0016-install-job-lifecycle.md`
- `docs/console/DESIGN.md`

## Comments
