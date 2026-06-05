# ADR-0008 — Budget-aware phased packaging

Source ADR: `docs/adr/ADR-0008-packaging.md`

## Goal

Support Phase 1 `uv`/`pipx` early-adopter installation immediately, while keeping package internals identical for later standalone bundle and signed/notarized distribution phases.

## Issues

1. [Document and test Phase 1 uv pipx install path](issues/01-document-and-test-phase-1-uv-pipx-install-path.md)
2. [Keep runtime paths packaging agnostic](issues/02-keep-runtime-paths-packaging-agnostic.md)
3. [Prepare Phase 2 and 3 packaging decision checklist](issues/03-prepare-phase-2-and-3-packaging-decision-checklist.md)
