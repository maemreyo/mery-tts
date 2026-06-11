# Doctor guidance for missing backend extras

Status: completed

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Add doctor output for backend state, selected backend, fallback reason, missing extras, and recovery guidance.

## Acceptance criteria

- [x] Doctor reports CPU-only, accelerated, missing-extra, and degraded states.
- [x] Guidance tells users what to install or configure.
- [x] Structured diagnostics align with backend schema.
- [x] Doctor does not require remote network access.

## Evidence required

- [x] Doctor command tests for each state.
- [x] Snapshot or structured output evidence.
- [x] Network-off test.

## Blocked by

- 03

## Evidence

- `src/mery_tts/hardware.py` defines backend capability, selection, probe, missing-extra, and safe fallback policy.
- `src/mery_tts/diagnostics/doctor.py` reports backend states without requiring accelerator hardware or network access.
- `tests/unit/test_hardware_backend_policy.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, and `tests/contract/test_api_core.py` cover backend selection, doctor guidance, and Console Developer Mode visibility for the static console.
- Verification: ADR-0042 focused verification previously recorded: hardware backend policy gate passed after Developer Mode remediation; current API/core verification remains green.
