# Create streaming package and core pipeline

Status: pending

## Parent

ADR-0031 — `docs/adr/ADR-0031-streaming-module-architecture.md`

## What to build

Create the standalone streaming subsystem and prove it with a deterministic fake streaming path. The slice should establish the package boundary, core pipeline orchestration, and fake test utilities without changing real provider behavior yet.

## Acceptance criteria

- [ ] `src/mery_tts/streaming/` exists with focused modules for config, metadata, sequence, cancellation, backpressure, pipeline, capabilities, and `transports/http.py`.
- [ ] A core pipeline can consume an `AsyncIterator[PCMChunk]` and expose a transport-independent ordered stream.
- [ ] Fake streaming utilities under `tests/fakes/streaming.py` can yield deterministic multi-chunk PCM streams for unit and contract tests.
- [ ] Existing blocking synthesis behavior remains unchanged.

## Production-ready criteria

- [ ] Unit tests cover the fake pipeline without booting FastAPI.
- [ ] The package exports only stable production primitives needed by API and tests.
- [ ] No production `src/mery_tts/streaming/testing.py` module is created.
- [ ] Route-local streaming lifecycle code is not added as part of this slice.

## Blocked by

- None - can start immediately
