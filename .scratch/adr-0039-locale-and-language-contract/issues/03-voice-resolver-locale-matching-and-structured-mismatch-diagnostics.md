# Voice resolver locale matching and structured mismatch diagnostics

Status: ready

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Teach voice resolution to match requested locale against supported voice locales with strict mismatch behavior and explicit fallback diagnostics. This is the runtime behavior slice; schema and validation are done in earlier slices.

Behavioral contract: Resolution prefers voices whose `supported_locales` contain the requested locale (exact or accepted fallback). On mismatch, a structured `locale_mismatch` error includes `requested_locale`, `voice_locales`, `mismatch_code`, and a sanitized reason. Explicit fallback succeeds only when policy permits; strict mismatch fails by default.

## Acceptance criteria

- [ ] Voice resolution logic checks `supported_locales` against request `locale`.
- [ ] Exact or normalized locale match succeeds.
- [ ] Mismatch produces structured `locale_mismatch` error with machine-readable code.
- [ ] Explicit fallback succeeds only when policy is permissive.
- [ ] Diagnostics include requested locale, selected locale, fallback reason, and blocked mismatch details without raw text.

## Evidence required

- Resolver unit tests for match, mismatch, and fallback scenarios.
- Structured `locale_mismatch` error taxonomy coverage.
- Diagnostics redaction test proving no raw text leakage.
- Fake-engine contract test proving resolver behavior under locale constraints.

## Blocked by

01-voice-and-catalog-bcp47-locale-metadata-schema.md
02-request-locale-field-and-backward-compatible-api-contract-tests.md
