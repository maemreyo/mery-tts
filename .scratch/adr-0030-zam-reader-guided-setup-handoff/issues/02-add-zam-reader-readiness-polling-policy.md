# Add Zam Reader readiness polling policy

Status: completed

## Parent

ADR-0030 — `docs/adr/ADR-0030-zam-reader-guided-setup-handoff.md`

## What to build

Define and document how Zam Reader should poll Mery readiness after setup handoff and when it may switch from Web Speech fallback to Mery synthesis.

## Acceptance criteria

- [x] Policy maps `/v1/health` unavailable, degraded, ready, unpaired, and incompatible states to Zam Reader behavior.
- [x] Degraded mode rules identify when experimental local synthesis is allowed.
- [x] Ready mode requires compatible contract, paired/authenticated helper, usable voices, and smoke evidence according to ADR-0025.
- [x] Zam Reader fallback to Web Speech remains required whenever Mery is unavailable or policy rejects degraded use.

## Production-ready criteria

- [x] Documentation cross-links ADR-0021, ADR-0025, ADR-0026, and ADR-0030.
- [x] Contract examples show polling response and client decision outcomes.
- [x] Tests or fixtures cover each readiness state and expected client action.

## Blocked by

- ADR-0025 issue 01-expand-health-to-layered-readiness-contract
- ADR-0026 issue 03-document-client-boundary-and-readiness-policy
