# Add voice-level fallback plan resolution

Status: completed

## Parent

ADR-0022 — `docs/adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`

## What to build

Resolve fallback at the voice level using request override, Mery user config, server defaults, and installed voice availability. The fallback plan should be provider-agnostic and ordered.

## Acceptance criteria

- [x] `VoiceFallbackPlan` or equivalent stores `primaryVoiceId`, ordered `fallbackVoiceIds`, and `fallbackPolicy`.
- [x] Request `mery` options can override config defaults.
- [x] Config defaults apply when request omits fallback options.
- [x] Server safe default or no fallback applies deterministically when neither request nor config specify fallback.
- [x] Fallback triggers only for recoverable provider/model/runtime/synthesis failures.

## Production-ready criteria

- [x] Pure unit tests cover precedence: request > config > safe default > none.
- [x] Tests prove fallback does not trigger for request validation, auth/security, cancellation, incompatible contract, text length, or unsupported format errors.
- [x] Attempted voices and final selected voice are included in sanitized diagnostics.

## Blocked by

- ADR-0022 issue 01-introduce-shared-speech-synthesis-service
