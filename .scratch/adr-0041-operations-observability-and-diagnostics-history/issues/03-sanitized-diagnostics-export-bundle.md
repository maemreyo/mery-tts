# Sanitized diagnostics export bundle

Status: needs-triage

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Expose a sanitized diagnostics export bundle through backend service, CLI, and console trigger/download.

## Acceptance criteria

- [ ] Bundle includes versions, platform, engine/provider health, installed voice summary, catalog summary, install states, readiness/smoke status, recent diagnostics, and audit summary.
- [ ] Bundle excludes raw input text, tokens, API keys, reference audio, model binaries, and unsanitized private paths.
- [ ] CLI and backend expose same behavior.
- [ ] Console can trigger/download export.

## Evidence required

- [ ] Export bundle contract test.
- [ ] Redaction tests.
- [ ] CLI/API/Console proof.

## Blocked by

- 02
