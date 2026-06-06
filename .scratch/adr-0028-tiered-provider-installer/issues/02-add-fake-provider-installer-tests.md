# Add fake ProviderInstaller tests

Status: completed

## Parent

ADR-0028 — `docs/adr/ADR-0028-tiered-provider-installer.md`

## What to build

Add fake ProviderInstaller adapters and service tests so setup orchestration can be tested without installing real provider packages.

## Acceptance criteria

- [x] Fake automatic installer can report missing, install successfully, fail install, and repair.
- [x] Fake guided installer returns user-safe manual steps and cannot auto-install.
- [x] Fake external installer reports externally managed runtime and explanation.
- [x] Setup/install services can consume fake installers through the protocol only.

## Production-ready criteria

- [x] Tests cover automatic success, automatic failure, guided-only flow, external runtime, and broken runtime repair plan.
- [x] No tests require real Piper, Kokoro, network, or platform-specific packages.
- [x] Fake installers are isolated to tests or test-support modules.

## Blocked by

- ADR-0028 issue 01-define-provider-installer-protocol
