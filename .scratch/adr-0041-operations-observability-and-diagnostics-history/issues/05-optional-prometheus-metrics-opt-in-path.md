# Optional Prometheus metrics opt-in path

Status: needs-triage

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Document and gate optional Prometheus-compatible local metrics for on-prem operators.

## Acceptance criteria

- [ ] Metrics are local-only and opt-in.
- [ ] No outbound telemetry is enabled by default.
- [ ] Docs list metric categories and privacy boundaries.
- [ ] Tests prove disabled-by-default and opt-in behavior.

## Evidence required

- [ ] Docs excerpt.
- [ ] Config tests for disabled/enabled states.
- [ ] No outbound telemetry assertion.

## Blocked by

- 03
