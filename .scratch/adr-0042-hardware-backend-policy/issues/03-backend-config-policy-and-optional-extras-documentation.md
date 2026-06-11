# Backend config policy and optional extras documentation

Status: completed

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Document base package, provider extras, backend extras, and network/privacy constraints for runtime dependencies.

## Acceptance criteria

- [x] Missing extras degrade gracefully instead of crashing.
- [x] `local_only` and `air_gapped` policies are respected.
- [x] No auto-download of runtime dependencies occurs.
- [x] Docs explain install commands or package extras.

## Evidence required

- [x] Docs excerpt.
- [x] Missing extras tests.
- [x] Network/no-auto-download assertion.

## Blocked by

- 01

## Evidence

- `src/mery_tts/hardware.py` defines backend capability, selection, probe, missing-extra, and safe fallback policy.
- `src/mery_tts/diagnostics/doctor.py` reports backend states without requiring accelerator hardware or network access.
- `tests/unit/test_hardware_backend_policy.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, and `tests/contract/test_api_core.py` cover backend selection, doctor guidance, and Console Developer Mode visibility for the static console.
- Verification: ADR-0042 focused verification previously recorded: hardware backend policy gate passed after Developer Mode remediation; current API/core verification remains green.
