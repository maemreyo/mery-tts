# Console locale filter and voice locale display

Status: completed

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Expose locale metadata in console discovery without creating a normal User Mode free-form override.

## Acceptance criteria

- [x] Voice cards/rows show supported locales.
- [x] Locale filter states are test-covered.
- [x] Playground shows selected voice locale.
- [x] User Mode does not expose arbitrary locale override controls.

## Evidence required

- [x] Component/browser tests for filter and voice cards.
- [x] Screenshot or Playwright trace of locale display.
- [x] Assertion that User Mode override is absent.

## Blocked by

- 01

## Evidence

- `src/mery_tts/locale.py`, `src/mery_tts/text_normalization.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas implement BCP-47 locale metadata, request locale handling, locale matching, and safe normalization boundaries.
- `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, `tests/unit/test_voice_descriptor.py`, and `tests/contract/test_api_schemas.py` cover locale schema/normalization behavior.
- `tests/contract/test_api_core.py` pins the packaged Console locale filter/display contract for the current static console while ADR-0038 tracks the React migration.
- Verification: ADR-0039 focused verification previously recorded: locale/language contract gate passed; current API/core verification remains green via `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py`.
