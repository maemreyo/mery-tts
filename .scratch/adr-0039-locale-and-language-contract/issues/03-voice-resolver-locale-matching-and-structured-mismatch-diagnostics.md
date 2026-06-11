# Voice resolver locale matching and structured mismatch diagnostics

Status: completed

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Teach voice resolution to match requested locale against supported voice locales with strict mismatch behavior and explicit fallback diagnostics. This is the runtime behavior slice; schema and validation are done in earlier slices.

Behavioral contract: Resolution prefers voices whose `supported_locales` contain the requested locale (exact or accepted fallback). On mismatch, a structured `locale_mismatch` error includes `requested_locale`, `voice_locales`, `mismatch_code`, and a sanitized reason. Explicit fallback succeeds only when policy permits; strict mismatch fails by default.

## Acceptance criteria

- [x] Voice resolution logic checks `supported_locales` against request `locale`.
- [x] Exact or normalized locale match succeeds.
- [x] Mismatch produces structured `locale_mismatch` error with machine-readable code.
- [x] Explicit fallback succeeds only when policy is permissive.
- [x] Diagnostics include requested locale, selected locale, fallback reason, and blocked mismatch details without raw text.

## Evidence required

- Resolver unit tests for match, mismatch, and fallback scenarios.
- Structured `locale_mismatch` error taxonomy coverage.
- Diagnostics redaction test proving no raw text leakage.
- Fake-engine contract test proving resolver behavior under locale constraints.

## Blocked by

01-voice-and-catalog-bcp47-locale-metadata-schema.md
02-request-locale-field-and-backward-compatible-api-contract-tests.md

## Evidence

- `src/mery_tts/locale.py`, `src/mery_tts/text_normalization.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas implement BCP-47 locale metadata, request locale handling, locale matching, and safe normalization boundaries.
- `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, `tests/unit/test_voice_descriptor.py`, and `tests/contract/test_api_schemas.py` cover locale schema/normalization behavior.
- `tests/contract/test_api_core.py` pins the packaged Console locale filter/display contract for the current static console while ADR-0038 tracks the React migration.
- Verification: ADR-0039 focused verification previously recorded: locale/language contract gate passed; current API/core verification remains green via `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py`.
