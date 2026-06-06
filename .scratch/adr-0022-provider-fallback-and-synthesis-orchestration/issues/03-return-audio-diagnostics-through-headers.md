# Return audio diagnostics through headers

Status: completed

## Parent

ADR-0022 — `docs/adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`

## What to build

Expose successful raw-audio diagnostics through `X-Mery-*` headers and reserve structured JSON bodies for failures. CORS must expose these headers to browser clients.

## Acceptance criteria

- [x] Successful `/v1/audio/speech` responses include request ID, selected voice, fallback-used flag, audio encoding, sample rate, and channel count headers.
- [x] Fallback success includes primary voice, fallback voice, and fallback reason headers.
- [x] Final failure returns structured JSON error body with attempted voices and sanitized diagnostic metadata.
- [x] `Access-Control-Expose-Headers` includes the required `X-Mery-*` headers.

## Production-ready criteria

- [x] Contract tests assert headers for normal success, fallback success, and final failure.
- [x] Browser-style CORS test proves JS can read exposed diagnostic headers.
- [x] Header values never include raw user text, filesystem paths, auth tokens, or page URLs.

## Blocked by

- ADR-0022 issue 01-introduce-shared-speech-synthesis-service
- ADR-0022 issue 02-add-voice-level-fallback-plan-resolution
