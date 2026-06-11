# Core locale normalization boundary and safe text transforms

Status: completed

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Define the core preprocessing boundary for locale-aware Unicode, punctuation, segmentation, and safe transformations before provider-specific hooks.

## Acceptance criteria

- [x] Core preprocessing handles Unicode normalization and punctuation normalization deterministically.
- [x] Sentence segmentation and max-length handling are locale-aware.
- [x] Provider phoneme/G2P hooks still run after core normalization.
- [x] Default diagnostics do not store raw or normalized text.

## Evidence required

- [x] Core preprocessing unit tests.
- [x] Provider adapter boundary tests with fake engine.
- [x] Sanitization test for normalization diagnostics.

## Blocked by

- 03

## Evidence

- `src/mery_tts/locale.py`, `src/mery_tts/text_normalization.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas implement BCP-47 locale metadata, request locale handling, locale matching, and safe normalization boundaries.
- `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, `tests/unit/test_voice_descriptor.py`, and `tests/contract/test_api_schemas.py` cover locale schema/normalization behavior.
- `tests/contract/test_api_core.py` pins the packaged Console locale filter/display contract for the current static console while ADR-0038 tracks the React migration.
- Verification: ADR-0039 focused verification previously recorded: locale/language contract gate passed; current API/core verification remains green via `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py`.
