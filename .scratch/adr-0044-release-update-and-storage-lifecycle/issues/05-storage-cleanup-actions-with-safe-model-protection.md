# Storage cleanup actions with safe model protection

Status: needs-triage

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Expose cleanup actions for caches, logs, and diagnostics while protecting active models and voices from auto-deletion.

## Acceptance criteria

- [ ] Cleanup actions exist for caches, logs, and diagnostics.
- [ ] Models/voices in active use are protected.
- [ ] CLI and Console expose cleanup commands/actions.
- [ ] Eviction is safe and auditable.

## Evidence required

- [ ] Cleanup tests.
- [ ] Active model protection tests.
- [ ] CLI/Console proof.
- [ ] Audit/diagnostics evidence.

## Blocked by

- 04
