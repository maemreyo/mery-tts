# Audio format policy and unsupported format errors

Status: completed

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Guarantee PCM/WAV in core and reject unsupported compressed formats without silent fallback.

## Acceptance criteria

- [x] Core guarantees PCM and WAV.
- [x] MP3, OGG, AAC, and Opus remain optional provider capabilities.
- [x] Unsupported formats return `unsupported_format`.
- [x] No silent fallback to another format occurs.

## Evidence required

- [x] Format negotiation tests.
- [x] Unsupported format error tests.
- [x] No-silent-fallback assertion.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/synthesis/service.py`, streaming pipeline/HTTP transport, and `src/mery_tts/text_normalization.py` implement provider concurrency/queue limits, timeout handling, disconnect cancellation, audio format rejection, segmentation, and sanitized normalization diagnostics.
- `tests/unit/test_streaming_lifecycle_policy.py`, `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, and `tests/contract/test_openai_speech.py` cover runtime resource policy behavior.
- Unsupported compressed formats are rejected with structured errors until explicit transcoding support is added.
- Verification: ADR-0045 focused verification previously recorded: runtime resource policy gate passed; current API/core verification remains green.
