# Request locale field and backward-compatible API contract tests

Status: completed

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Add optional request-level `locale` selection for synthesis while preserving current missing-locale behavior. The speech request schema accepts an optional `locale` field validated against BCP-47 rules. When omitted, resolution falls back to the voice's default behavior. When provided with invalid format, a structured validation error is returned.

Behavioral contract: Clients can send `locale: "vi-VN"` (or omit it) with a synthesis request. The resolver later uses this to select voices. Missing locale follows existing behavior.

## Acceptance criteria

- [x] Speech request schema accepts optional `locale` field without changing required fields.
- [x] Missing locale falls back to voice default behavior.
- [x] Request validation rejects malformed locale values with structured errors.
- [x] Backward-compatible `/v1` serialization tests prove older clients remain compatible.
- [x] API contract tests cover missing, valid, and invalid locale scenarios.

## Evidence required

- API contract test diff showing `/v1/audio/speech` accepts/returns locale correctly.
- Backward-compatible serialization test showing old client payload still works.
- Structured error taxonomy coverage for locale validation failures.

## Blocked by

01-voice-and-catalog-bcp47-locale-metadata-schema.md

## Evidence

- `src/mery_tts/locale.py`, `src/mery_tts/text_normalization.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas implement BCP-47 locale metadata, request locale handling, locale matching, and safe normalization boundaries.
- `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, `tests/unit/test_voice_descriptor.py`, and `tests/contract/test_api_schemas.py` cover locale schema/normalization behavior.
- `tests/contract/test_api_core.py` pins the packaged Console locale filter/display contract for the current static console while ADR-0038 tracks the React migration.
- Verification: ADR-0039 focused verification previously recorded: locale/language contract gate passed; current API/core verification remains green via `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py`.
