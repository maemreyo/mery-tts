# Explicit update confirmation and integrity policy

Status: needs-triage

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Require explicit user/admin action for catalog refresh and model downloads with checksum/signature validation and policy checks.

## Acceptance criteria

- [ ] No silent app/catalog/model auto-update occurs.
- [ ] Console/CLI show source, size, license, version, and capability impact before install.
- [ ] `local_only` and `air_gapped` block network updates.
- [ ] Checksum/signature validation failures are structured and recoverable.

## Evidence required

- [ ] CLI/Console confirmation tests.
- [ ] Integrity validation tests.
- [ ] Network-policy enforcement tests.

## Blocked by

- 01
