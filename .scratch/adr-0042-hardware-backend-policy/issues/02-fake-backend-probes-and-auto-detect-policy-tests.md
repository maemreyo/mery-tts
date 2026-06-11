# Fake backend probes and auto-detect policy tests

Status: needs-triage

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Use fake backend probes to test available, unavailable, and degraded backend auto-detection without real accelerator hardware.

## Acceptance criteria

- [ ] Auto-detect chooses safest supported backend by default.
- [ ] Per-provider override takes precedence over global default.
- [ ] Invalid override yields structured diagnostics and safe fallback.
- [ ] Tests require no GPU/accelerator hardware.

## Evidence required

- [ ] Fake probe test matrix.
- [ ] Override precedence tests.
- [ ] Invalid override diagnostics test.

## Blocked by

- 01
