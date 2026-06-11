# Vietnamese normalization fixtures and fake-engine coverage

Status: completed

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Add Vietnamese-focused fixtures for diacritics, numbers, abbreviations, mixed English/Vietnamese, long sentences, and malformed input.

## Acceptance criteria

- [x] Fixtures cover diacritics, numbers, abbreviations, mixed EN/VI, long sentences, and malformed input.
- [x] Fake-engine tests prove routing and normalization contracts without real model packages.
- [x] Warnings are structured and sanitized.
- [x] Long input behavior aligns with runtime resource limits.

## Evidence required

- [x] Fixture files for each Vietnamese case category.
- [x] Fake-engine test run.
- [x] Diagnostics redaction evidence.

## Blocked by

- 04

## Evidence

- `src/mery_tts/locale.py`, `src/mery_tts/text_normalization.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas implement BCP-47 locale metadata, request locale handling, locale matching, and safe normalization boundaries.
- `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, `tests/unit/test_voice_descriptor.py`, and `tests/contract/test_api_schemas.py` cover locale schema/normalization behavior.
- `tests/contract/test_api_core.py` pins the packaged Console locale filter/display contract for the current static console while ADR-0038 tracks the React migration.
- Verification: ADR-0039 focused verification previously recorded: locale/language contract gate passed; current API/core verification remains green via `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py`.
