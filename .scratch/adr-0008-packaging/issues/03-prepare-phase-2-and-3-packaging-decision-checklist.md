# Prepare Phase 2 and 3 packaging decision checklist

Status: ready-for-human

## Parent

ADR-0008 — `docs/adr/ADR-0008-packaging.md`

## What to build

Create the human review checklist for moving beyond Phase 1, including unsigned standalone bundle implications, honest Gatekeeper instructions, and budget-dependent signed/notarized distribution criteria.

## Acceptance criteria

- [x] Checklist documents Phase 2 unsigned bundle options and expected Gatekeeper UX. ADR-0008 documents Phase 2 unsigned bundle distribution via PyInstaller/Nuitka with expected Gatekeeper "unidentified developer" UX and user right-click override.
- [x] Checklist documents Phase 3 signing/notarization requirements and budget trigger. ADR-0008 documents Phase 3 Apple Developer Program ($99/year) for signing/notarization as the budget trigger for seamless UX.
- [x] No Phase 2/3 plan requires changing helper internals between packaging modes. ADR-0008 and ADR-0002 confirm runtime paths use platform app-data locations (`RuntimePaths`) and no package-relative writable paths; helper internals are packaging-agnostic.
- [x] Docs identify which user-facing setup copy Zam Reader must show for each packaging phase. ADR-0008 and README Phase 1 quickstart document the setup UX for each phase; Zam Reader integration uses `/v1` bridge contract regardless of packaging mode.

## Blocked by

- 01-document-and-test-phase-1-uv-pipx-install-path
- 02-keep-runtime-paths-packaging-agnostic

## Comments
