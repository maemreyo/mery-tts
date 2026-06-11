# Backend capability and selection schema

Status: completed

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Represent supported backends, selected backend, fallback reason, and missing optional extras with global default plus per-provider override.

## Acceptance criteria

- [x] Schema includes supported candidates, selected backend, fallback reason, and missing extras.
- [x] Global default and per-provider override are supported.
- [x] No per-voice backend complexity is introduced.
- [x] Serialization is additive and backward-compatible.

## Evidence required

- [x] Schema excerpt.
- [x] Serialization tests.
- [x] Config fixture tests.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/hardware.py` defines backend capability, selection, probe, missing-extra, and safe fallback policy.
- `src/mery_tts/diagnostics/doctor.py` reports backend states without requiring accelerator hardware or network access.
- `tests/unit/test_hardware_backend_policy.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, and `tests/contract/test_api_core.py` cover backend selection, doctor guidance, and Console Developer Mode visibility for the static console.
- Verification: ADR-0042 focused verification previously recorded: hardware backend policy gate passed after Developer Mode remediation; current API/core verification remains green.
