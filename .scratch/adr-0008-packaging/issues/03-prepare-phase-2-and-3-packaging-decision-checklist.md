# Prepare Phase 2 and 3 packaging decision checklist

Status: ready-for-human

## Parent

ADR-0008 — `docs/adr/ADR-0008-packaging.md`

## What to build

Create the human review checklist for moving beyond Phase 1, including unsigned standalone bundle implications, honest Gatekeeper instructions, and budget-dependent signed/notarized distribution criteria.

## Acceptance criteria

- [ ] Checklist documents Phase 2 unsigned bundle options and expected Gatekeeper UX.
- [ ] Checklist documents Phase 3 signing/notarization requirements and budget trigger.
- [ ] No Phase 2/3 plan requires changing helper internals between packaging modes.
- [ ] Docs identify which user-facing setup copy Zam Reader must show for each packaging phase.

## Blocked by

- 01-document-and-test-phase-1-uv-pipx-install-path
- 02-keep-runtime-paths-packaging-agnostic

## Comments
