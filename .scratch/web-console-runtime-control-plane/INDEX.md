# Web Console Runtime Control Plane Issue Set

Status: ready-for-agent

## Purpose

Track implementation issues for the Web Console Runtime Control Plane ADR set.

## ADRs

- ADR-0052 — Web Console Runtime Control Plane
- ADR-0053 — Overview Guided Recovery and Status
- ADR-0054 — Console Connection Module and Shared Query Keys
- ADR-0055 — Responsive Voices Table and Card Presentation
- ADR-0056 — Playground Installed Voice Picker and Raw ID Override
- ADR-0057 — Diagnostics-Ready Health and Developer Schema Preview
- ADR-0058 — Console Test, Accessibility, and Visual QA Gates

## Dependency order

Issues with no `Blocked by` can run in parallel.

```
10 (nav model)   12 (error boundaries)   13 (dep cleanup)
      ↓
      01 (API wrapper + freshness)
      ↓
      09 (MSW + test utilities)
      ↓
      02 (connection module + query keys)
      ↓ ──────────────────────────────────────────────────────────────────┐
      03 (overview)   04 (voices)   05 (health)   06 (playground)   07 (developer)
           ↓                                                               ↓
      11 (topbar compact)          ←─────────────────────────────────────┘
           └──────────────────────────────────────────────────────────────┐
                                                                          08 (QA gates)
```

## Issues

| # | File | Blocked by |
|---|------|-----------|
| 01 | `issues/01-runtime-control-plane-api-wrapper-and-freshness.md` | — |
| 02 | `issues/02-connection-module-and-query-keys.md` | 01 |
| 03 | `issues/03-overview-guided-recovery-and-status.md` | 01, 02, 10 |
| 04 | `issues/04-voices-table-cards-and-install-recovery.md` | 01, 02, 09 |
| 05 | `issues/05-health-diagnostics-ready-status-view.md` | 01, 02, 09 |
| 06 | `issues/06-playground-installed-picker-and-advanced-raw-id.md` | 01, 02, 09 |
| 07 | `issues/07-developer-schema-preview.md` | 01, 05 |
| 08 | `issues/08-console-test-a11y-and-visual-qa-gates.md` | 03, 04, 05, 06, 07, 11 |
| 09 | `issues/09-msw-vitest-setup-and-shared-test-utilities.md` | 01 |
| 10 | `issues/10-navigation-model-add-overview-section.md` | — |
| 11 | `issues/11-topbar-compact-status-and-reconnect.md` | 02 |
| 12 | `issues/12-per-panel-error-boundaries.md` | — |
| 13 | `issues/13-dependency-cleanup-remove-unused-packages.md` | — |

## Notes for agents

- Implement only the issue being worked.
- Do not add backend endpoints unless an issue explicitly says so; v1 must adapt to existing
  Console capabilities.
- Do not expose server URL/base path UI in v1.
- Do not show last install job or persisted smoke result on Overview v1.
- Keep generated API code quarantined; feature components must use wrappers/view models.
- UI completion requires component tests, accessibility evidence, and real browser/visual proof
  where applicable.
- All test fixtures must use synthetic data — no real bearer tokens, no real IP addresses,
  no private filesystem paths, no real user input.
