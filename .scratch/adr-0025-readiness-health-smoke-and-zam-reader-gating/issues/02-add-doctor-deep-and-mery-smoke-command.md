# Add doctor --deep and mery smoke command

Status: completed

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Add explicit deep smoke commands that run real synthesis through the same service path as normal requests and record per-voice smoke results.

## Acceptance criteria

- [x] `mery doctor` performs non-synthesis dependency/artifact/voice readiness checks by default.
- [x] `mery doctor --deep` runs real synthesis smoke for selected or configured voices.
- [x] `mery smoke --providers piper-plus,kokoro` or equivalent command runs provider-specific smoke checks.
- [x] Smoke uses `SpeechSynthesisService` with `purpose="smoke"` context and does not mutate user defaults.

## Production-ready criteria

- [x] CLI tests cover default doctor, deep doctor, smoke success, smoke failure, and missing voice behavior with fake runtimes.
- [x] Smoke text is locale-appropriate where available and never logged raw.
- [x] Smoke warms runtime cache but only persists smoke metadata.

## Blocked by

- ADR-0022 issue 01-introduce-shared-speech-synthesis-service
- ADR-0024 issues 02-add-piper-runtime-cache-and-real-adapter-path and 03-add-kokoro-runtime-cache-and-real-adapter-path
