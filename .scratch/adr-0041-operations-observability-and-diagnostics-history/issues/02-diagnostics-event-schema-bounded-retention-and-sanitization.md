# Diagnostics event schema bounded retention and sanitization

Status: needs-triage

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Type

AFK

## What to build

Add bounded sanitized diagnostics history covering runtime, install, readiness, synthesis metadata, fallback, cancellation, and errors.

## Acceptance criteria

- [ ] Event schema covers startup/shutdown, discovery, provider health, install lifecycle, readiness transitions, smoke, synthesis metadata, fallback, cancellation, and sanitized errors.
- [ ] Default retention is 7 days or 1,000 events.
- [ ] Corrupt storage does not break synthesis.
- [ ] Raw text, tokens, audio, keys, and private paths are redacted.

## Evidence required

- [ ] Retention tests.
- [ ] Storage corruption test.
- [ ] Redaction matrix tests.

## Blocked by

- 01
