# Add metadata and sequence validation tests

Status: pending

## Parent

ADR-0032 — `docs/adr/ADR-0032-pcm-chunk-streaming-contract.md`

## What to build

Add streaming metadata and sequence validation primitives that establish the stream contract from the first chunk and reject later drift or ordering errors deterministically.

## Acceptance criteria

- [ ] First chunk establishes sample rate, channels, sample width, and encoding.
- [ ] Later chunks with metadata drift are rejected by the streaming subsystem.
- [ ] The streaming pipeline assigns transport sequence numbers for adapters emitting default `0` sequence values.
- [ ] Sequence validation detects duplicate, missing, or out-of-order chunks when explicit non-zero adapter sequences are provided.
- [ ] Migration behavior for adapters emitting default sequence values is explicit and tested.

## Production-ready criteria

- [ ] Unit tests cover valid streams, first-chunk invalid metadata, post-start metadata drift, all-zero adapter sequence assignment, monotonic explicit sequence, and out-of-order explicit sequence.
- [ ] HTTP-facing validation rejects `pcm_f32le` before first byte and treats encoding drift after body start as metadata drift.
- [ ] Validation errors are typed or classified for HTTP lifecycle handling.
- [ ] The validation code is transport-independent.

## Blocked by

- `01-upgrade-pcmchunk-with-streaming-metadata.md`
