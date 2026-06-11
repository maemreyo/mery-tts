# Long text max length segmentation and normalization diagnostics

Status: completed

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Enforce max length, locale-aware segmentation, structured long-input errors, and sanitized normalization diagnostics.

## Acceptance criteria

- [x] Core enforces max text length.
- [x] Locale-aware segmentation splits long input safely where supported.
- [x] Unsupported long input returns structured errors.
- [x] Diagnostics include locale, normalizer version, categories, warnings, and length metadata without raw text.

## Evidence required

- [x] Max-length tests.
- [x] Segmentation tests.
- [x] Diagnostic redaction tests.
- [x] Progress/cancellation tests where segmented synthesis exists.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/synthesis/service.py`, streaming pipeline/HTTP transport, and `src/mery_tts/text_normalization.py` implement provider concurrency/queue limits, timeout handling, disconnect cancellation, audio format rejection, segmentation, and sanitized normalization diagnostics.
- `tests/unit/test_streaming_lifecycle_policy.py`, `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, and `tests/contract/test_openai_speech.py` cover runtime resource policy behavior.
- Unsupported compressed formats are rejected with structured errors until explicit transcoding support is added.
- Verification: ADR-0045 focused verification previously recorded: runtime resource policy gate passed; current API/core verification remains green.
