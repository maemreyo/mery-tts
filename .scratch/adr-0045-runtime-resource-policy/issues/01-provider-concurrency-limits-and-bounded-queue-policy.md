# Provider concurrency limits and bounded queue policy

Status: completed

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Add per-provider/engine concurrency limits with bounded queueing, overflow errors, timeout handling, and cancellation slot release.

## Acceptance criteria

- [x] Each provider/engine has a concurrency limit.
- [x] Requests beyond active limit enter bounded queue or fail with `busy`/`rate_limited`.
- [x] No unbounded threads or queues are introduced.
- [x] Cancellation releases slots.

## Evidence required

- [x] Queue overflow tests.
- [x] Slot release tests.
- [x] Structured busy/rate-limited error tests.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/synthesis/service.py`, streaming pipeline/HTTP transport, and `src/mery_tts/text_normalization.py` implement provider concurrency/queue limits, timeout handling, disconnect cancellation, audio format rejection, segmentation, and sanitized normalization diagnostics.
- `tests/unit/test_streaming_lifecycle_policy.py`, `tests/unit/test_text_normalization.py`, `tests/unit/test_vietnamese_normalization_fixtures.py`, and `tests/contract/test_openai_speech.py` cover runtime resource policy behavior.
- Unsupported compressed formats are rejected with structured errors until explicit transcoding support is added.
- Verification: ADR-0045 focused verification previously recorded: runtime resource policy gate passed; current API/core verification remains green.
