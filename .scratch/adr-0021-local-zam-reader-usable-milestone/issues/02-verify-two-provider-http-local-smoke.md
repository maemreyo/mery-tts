# Verify two-provider HTTP local smoke

Status: planned

## Parent

ADR-0021 — `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`

## What to build

Create an end-to-end local smoke path that proves Piper and Kokoro can both synthesize through HTTP `/v1/audio/speech`, and that Mery can operate degraded when only one provider works.

## Acceptance criteria

- [ ] Piper installed voice synthesizes real WAV or PCM through `/v1/audio/speech`.
- [ ] Kokoro installed voice synthesizes real WAV or PCM through `/v1/audio/speech`.
- [ ] Piper→Kokoro fallback is exercised when Piper fails recoverably.
- [ ] Runtime degraded mode still allows synthesis through the working provider.

## Production-ready criteria

- [ ] Real-helper smoke test records request IDs, selected voice, fallback status, audio metadata, and sanitized failure details.
- [ ] Smoke verifies non-empty valid audio and stable sample-rate/channel metadata.
- [ ] `tools/audio-test/run_speech.py` or equivalent exits 0 when both providers are installed and real synthesis succeeds.

## Blocked by

- ADR-0022 issue 01-introduce-shared-speech-synthesis-service
- ADR-0023 issue 03-complete-async-install-worker-for-bundled-artifacts
- ADR-0024 issues 02-add-piper-runtime-cache-and-real-adapter-path and 03-add-kokoro-runtime-cache-and-real-adapter-path
