# Streaming disconnect cancellation and first-byte fallback rules

Status: completed

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Handle client disconnects, resource release, and phase-aware fallback: fallback before first byte only, structured termination after first byte.

## Acceptance criteria

- [x] Client disconnect cancels synthesis and releases resources.
- [x] Diagnostics include `cancelled_by=client_disconnect`.
- [x] Fallback is allowed only before first byte.
- [x] After first byte, stream ends with structured failure/cancellation diagnostics.

## Evidence required

- [x] Streaming route disconnect tests.
- [x] Fallback state-machine tests.
- [x] Resource release tests.
- [x] Diagnostics tests.

## Blocked by

- 01
- 02

## Evidence

- `src/mery_tts/synthesis/service.py`, streaming pipeline/HTTP transport, and `src/mery_tts/text_normalization.py` implement provider concurrency/queue limits, timeout handling, disconnect cancellation, audio format rejection, segmentation, and sanitized normalization diagnostics.
- `tests/unit/test_streaming_lifecycle_policy.py`, `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, and `tests/contract/test_openai_speech.py` cover runtime resource policy behavior.
- Unsupported compressed formats are rejected with structured errors until explicit transcoding support is added.
- Verification: ADR-0045 focused verification previously recorded: runtime resource policy gate passed; current API/core verification remains green.
