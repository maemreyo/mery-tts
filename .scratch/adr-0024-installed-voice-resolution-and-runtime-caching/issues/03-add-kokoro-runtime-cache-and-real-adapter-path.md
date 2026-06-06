# Add Kokoro runtime cache and real adapter path

Status: completed

## Parent

ADR-0024 — `docs/adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`

## What to build

Replace the Kokoro adapter stub with a real resolved-voice synthesis path that lazy-loads Kokoro runtime objects and caches them per installed voice/artifact.

## Acceptance criteria

- [x] Kokoro adapter accepts resolved preset/shared-artifact voices with required model/voice files.
- [x] Runtime loading validates dependency availability and required preset assets.
- [x] Adapter emits normalized `PCMChunk` values only.
- [x] Runtime cache reuses loaded Kokoro runtime for repeated synthesis of the same voice.
- [x] Library-specific exceptions map to structured Mery domain errors.

## Production-ready criteria

- [x] Unit tests use fake Kokoro runtime to verify load, synthesize, cache reuse, dependency missing, invalid asset, and synthesis failure paths.
- [x] Engine-marked smoke test can run against a real bundled/local Kokoro artifact when dependency is installed.
- [x] Kokoro can act as fallback for Piper in service-level tests.

## Blocked by

- ADR-0024 issue 01-introduce-installed-voice-resolver
