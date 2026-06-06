# Add Kokoro runtime cache and real adapter path

Status: planned

## Parent

ADR-0024 — `docs/adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`

## What to build

Replace the Kokoro adapter stub with a real resolved-voice synthesis path that lazy-loads Kokoro runtime objects and caches them per installed voice/artifact.

## Acceptance criteria

- [ ] Kokoro adapter accepts resolved preset/shared-artifact voices with required model/voice files.
- [ ] Runtime loading validates dependency availability and required preset assets.
- [ ] Adapter emits normalized `PCMChunk` values only.
- [ ] Runtime cache reuses loaded Kokoro runtime for repeated synthesis of the same voice.
- [ ] Library-specific exceptions map to structured Mery domain errors.

## Production-ready criteria

- [ ] Unit tests use fake Kokoro runtime to verify load, synthesize, cache reuse, dependency missing, invalid asset, and synthesis failure paths.
- [ ] Engine-marked smoke test can run against a real bundled/local Kokoro artifact when dependency is installed.
- [ ] Kokoro can act as fallback for Piper in service-level tests.

## Blocked by

- ADR-0024 issue 01-introduce-installed-voice-resolver
