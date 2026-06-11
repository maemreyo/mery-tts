# Timeout defaults overrides and structured timeout errors

Status: completed

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Implement global, per-provider, and request-level timeout policy with cleanup and structured timeout errors.

## Acceptance criteria

- [x] Global default and per-provider override exist.
- [x] Normal clients can request shorter timeout but cannot extend indefinitely.
- [x] Admin/config can raise limits.
- [x] Timeout triggers cancellation/cleanup and structured error.

## Evidence required

- [x] Timeout override tests.
- [x] Request lower-bound tests.
- [x] Cleanup tests.
- [x] Structured timeout error tests.

## Blocked by

- 01

## Evidence

- `src/mery_tts/synthesis/service.py`, streaming pipeline/HTTP transport, and `src/mery_tts/text_normalization.py` implement provider concurrency/queue limits, timeout handling, disconnect cancellation, audio format rejection, segmentation, and sanitized normalization diagnostics.
- `tests/unit/test_streaming_lifecycle_policy.py`, `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, and `tests/contract/test_openai_speech.py` cover runtime resource policy behavior.
- Unsupported compressed formats are rejected with structured errors until explicit transcoding support is added.
- Verification: ADR-0045 focused verification previously recorded: runtime resource policy gate passed; current API/core verification remains green.
