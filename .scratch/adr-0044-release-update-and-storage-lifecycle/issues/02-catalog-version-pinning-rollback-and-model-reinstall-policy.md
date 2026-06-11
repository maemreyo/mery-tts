# Catalog version pinning rollback and model reinstall policy

Status: needs-triage

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Pin catalog versions, rollback to previous valid catalog, and handle corrupt model artifacts by reinstalling same version.

## Acceptance criteria

- [ ] Catalog refresh stores previous valid version.
- [ ] Rollback restores previous valid catalog.
- [ ] Corrupt model artifacts are marked corrupt and reinstalled at same version.
- [ ] Model rollback is deferred pending storage policy.

## Evidence required

- [ ] Catalog rollback tests.
- [ ] Corrupt artifact reinstall tests.
- [ ] State transition evidence.

## Blocked by

- 01
