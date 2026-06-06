# Define setup intent contract

Status: planned

## Parent

ADR-0026 — `docs/adr/ADR-0026-standalone-setup-boundary.md`

## What to build

Define a client-agnostic setup intent contract so Zam Reader and future clients can request local voice setup without owning provider install logic.

## Acceptance criteria

- [ ] Setup intent accepts client identity, use-case intent, locale preference, and optional return context without exposing raw filesystem paths.
- [ ] Invalid or unknown client/intent values return structured sanitized errors.
- [ ] Setup intent can be represented as a local console URL and as an internal service request.
- [ ] Zam Reader-specific values are examples, not hardcoded domain concepts.

## Production-ready criteria

- [ ] Contract tests cover valid Zam Reader intent, unknown client, unknown intent, missing auth, and malformed query parameters.
- [ ] Docs describe client responsibilities versus Mery responsibilities.
- [ ] No install action is triggered by parsing intent alone.

## Blocked by

- None - can start immediately
