# Add Piper runtime cache and real adapter path

Status: planned

## Parent

ADR-0024 — `docs/adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`

## What to build

Replace the Piper adapter stub with a real resolved-voice synthesis path that lazy-loads Piper/Piper-plus runtime objects and caches them per installed voice/artifact.

## Acceptance criteria

- [ ] Piper adapter accepts resolved model-file voices with model/config paths.
- [ ] Runtime loading uses the correct Piper/Piper-plus Python API and validates dependency availability.
- [ ] Adapter emits normalized `PCMChunk` values only; it does not wrap WAV or serialize HTTP responses.
- [ ] Runtime cache reuses loaded Piper runtime for repeated synthesis of the same voice.
- [ ] Library-specific exceptions map to structured Mery domain errors.

## Production-ready criteria

- [ ] Unit tests use fake Piper runtime to verify load, synthesize, cache reuse, dependency missing, invalid model, and synthesis failure paths.
- [ ] Engine-marked smoke test can run against a real bundled/local Piper artifact when dependency is installed.
- [ ] No raw `RuntimeError` string is exposed on production synthesis failure.

## Blocked by

- ADR-0024 issue 01-introduce-installed-voice-resolver
