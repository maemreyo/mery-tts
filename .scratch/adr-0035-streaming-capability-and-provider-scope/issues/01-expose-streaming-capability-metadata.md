# Expose streaming capability metadata

Status: pending

## Parent

ADR-0035 — `docs/adr/ADR-0035-streaming-capability-and-provider-scope.md`

## What to build

Expose truthful streaming capability metadata through existing `/v1/engines` and `/v1/voices/installed` discovery so clients can know whether an engine or installed voice supports streaming, what mode it uses, and whether it is truly incremental.

## Acceptance criteria

- [ ] Capability taxonomy includes not supported, route chunked, sentence chunked, and native incremental modes.
- [ ] `/v1/engines` serializes engine-level baseline plus runtime streaming capability.
- [ ] `/v1/voices/installed` serializes effective voice-level streaming capability.
- [ ] Capability data includes support, mode, granularity, true-incremental flag, supported format, and sample rates.
- [ ] `/v1/audio/speech` behavior remains stable and does not require capability negotiation.
- [ ] No new streaming capability endpoint is created.
- [ ] P1 does not expose hard latency or preferred chunk-size controls.

## Production-ready criteria

- [ ] API/schema tests cover snake_case capability serialization.
- [ ] Tests prove adapter baseline, installed voice/model metadata, and runtime health combine into effective capability.
- [ ] Unsupported/deferred providers can be represented without special-case route behavior.
- [ ] Docs explain how clients should use capability metadata.

## Blocked by

- ADR-0032 issue `01-upgrade-pcmchunk-with-streaming-metadata.md`
