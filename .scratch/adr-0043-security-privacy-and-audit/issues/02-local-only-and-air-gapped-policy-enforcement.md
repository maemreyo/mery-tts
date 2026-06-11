# Local-only and air-gapped policy enforcement

Status: needs-triage

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Enforce `local_only` and `air_gapped` before catalog refresh, remote provider calls, and model downloads.

## Acceptance criteria

- [ ] Remote catalog refresh is blocked when policy requires local-only/air-gapped.
- [ ] Remote provider calls are blocked with structured errors.
- [ ] Model downloads are blocked with user-actionable diagnostics.
- [ ] Console clearly shows network operations disabled.

## Evidence required

- [ ] Catalog/provider/install enforcement tests.
- [ ] Structured error tests.
- [ ] Console UI test for disabled network operations.

## Blocked by

None - can start immediately
