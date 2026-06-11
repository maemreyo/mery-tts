# Fake backend probes and auto-detect policy tests

Status: completed

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Use fake backend probes to test available, unavailable, and degraded backend auto-detection without real accelerator hardware.

## Acceptance criteria

- [x] Auto-detect chooses safest supported backend by default.
- [x] Per-provider override takes precedence over global default.
- [x] Invalid override yields structured diagnostics and safe fallback.
- [x] Tests require no GPU/accelerator hardware.

## Evidence required

- [x] Fake probe test matrix.
- [x] Override precedence tests.
- [x] Invalid override diagnostics test.

## Blocked by

- 01

## Evidence

- `src/mery_tts/hardware.py` defines backend capability, selection, probe, missing-extra, and safe fallback policy.
- `src/mery_tts/diagnostics/doctor.py` reports backend states without requiring accelerator hardware or network access.
- `tests/unit/test_hardware_backend_policy.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, and `tests/contract/test_api_core.py` cover backend selection, doctor guidance, and Console Developer Mode visibility for the static console.
- Verification: ADR-0042 focused verification previously recorded: hardware backend policy gate passed after Developer Mode remediation; current API/core verification remains green.
