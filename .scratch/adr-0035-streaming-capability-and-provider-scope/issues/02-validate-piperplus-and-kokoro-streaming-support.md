# Validate PiperPlus and Kokoro streaming support

Status: pending

## Parent

ADR-0035 — `docs/adr/ADR-0035-streaming-capability-and-provider-scope.md`

## What to build

Validate PiperPlus and Kokoro as the first real providers supported by the generic streaming contract, while explicitly deferring Supertonic and avoiding false promises of true incremental streaming.

## Acceptance criteria

- [ ] PiperPlus emits richer `PCMChunk` values through the existing `synthesize()` contract.
- [ ] Kokoro emits richer `PCMChunk` values through the existing `synthesize()` contract.
- [ ] PiperPlus and Kokoro capability metadata accurately reports route-chunked or sentence-chunked support from adapter baseline, installed voice/model metadata, and runtime health.
- [ ] Capability mode serialization uses snake_case enum values.
- [ ] Supertonic is represented as deferred or unsupported for P1, not silently treated as implemented.

## Production-ready criteria

- [ ] Fake streaming contract tests remain the primary P1 proof.
- [ ] Real PiperPlus and Kokoro streaming validation is covered where runtime dependencies are available, or marked as a release gate when optional dependencies are absent.
- [ ] Tests cover a provider yielding a single chunk and a provider yielding multiple chunks under the same generic contract.
- [ ] Tests prove the route still works when a provider yields a single chunk, so protocol streaming does not depend on true incremental synthesis.

## Blocked by

- `01-expose-streaming-capability-metadata.md`
- ADR-0034 issue `01-emit-audio-l16-first-chunk-derived-http-stream.md`
