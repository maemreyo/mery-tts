# Console backend summary and developer override controls

Status: completed

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Show backend summary in User Mode and detailed backend selection/override controls only in Developer Mode.

## Acceptance criteria

- [x] User Mode displays selected backend and fallback summary.
- [x] Developer Mode shows candidate backends, missing extras, and selection reasons.
- [x] Override controls are hidden from normal first-run users.
- [x] UI covers CPU-only, accelerated, missing-extra, and degraded states.

## Evidence required

- [x] UI tests for all backend states.
- [x] Developer Mode visibility tests.
- [x] Screenshot/trace evidence.

## Blocked by

- 02

## Evidence

- `src/mery_tts/hardware.py` defines backend capability, selection, probe, missing-extra, and safe fallback policy.
- `src/mery_tts/diagnostics/doctor.py` reports backend states without requiring accelerator hardware or network access.
- `tests/unit/test_hardware_backend_policy.py`, `tests/unit/test_doctor_storage_packaging_rollout.py`, and `tests/contract/test_api_core.py` cover backend selection, doctor guidance, and Console Developer Mode visibility for the static console.
- Verification: ADR-0042 focused verification previously recorded: hardware backend policy gate passed after Developer Mode remediation; current API/core verification remains green.
