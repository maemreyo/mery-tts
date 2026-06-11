# Voice and catalog BCP-47 locale metadata schema

Status: completed

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Add additive BCP-47 locale metadata to voice and catalog projections so clients can discover language support without parsing names or engine IDs. The change introduces `supported_locales` as an additive array field on voice descriptors and catalog entries, validated against BCP-47 format and normalized before storage.

Behavioral contract: Each voice/catalog entry may expose one or more locale tags (`vi-VN`, `en-US`, `en-GB`). Clients read `supported_locales` to filter voices or warn users about locale mismatches. Absent or unrecognized locales do not break consumption.

## Acceptance criteria

- [x] Voice descriptor schema exposes additive `supported_locales` array field.
- [x] Catalog projection schema exposes additive `supported_locales` on category entries.
- [x] Valid `vi-VN`, `en-US`, and `en-GB` tags are accepted and normalized.
- [x] Malformed tags are rejected at schema boundaries with structured errors.
- [x] Backward-compatible serialization proves old voice payloads without locale still work.

## Evidence required

- Schema/API excerpt showing additive `supported_locales` fields.
- Unit tests for valid and invalid BCP-47 tags.
- Serialization tests proving backward compatibility.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/locale.py`, `src/mery_tts/text_normalization.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas implement BCP-47 locale metadata, request locale handling, locale matching, and safe normalization boundaries.
- `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, `tests/unit/test_voice_descriptor.py`, and `tests/contract/test_api_schemas.py` cover locale schema/normalization behavior.
- `tests/contract/test_api_core.py` pins the packaged Console locale filter/display contract for the current static console while ADR-0038 tracks the React migration.
- Verification: ADR-0039 focused verification previously recorded: locale/language contract gate passed; current API/core verification remains green via `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py`.
