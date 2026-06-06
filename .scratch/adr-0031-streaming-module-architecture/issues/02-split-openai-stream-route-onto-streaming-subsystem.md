# Split OpenAI stream route onto streaming subsystem

Status: pending

## Parent

ADR-0031 — `docs/adr/ADR-0031-streaming-module-architecture.md`

## What to build

Refactor the existing `/v1/audio/speech` `stream=true` path so the route delegates streaming lifecycle behavior to the standalone streaming subsystem instead of owning generator, metadata, cancellation, or response semantics inline.

## Acceptance criteria

- [ ] The route keeps request validation, voice/adapter context assembly, and response return only.
- [ ] Streaming metadata, cancellation, backpressure, error lifecycle, and HTTP adaptation live outside `api/app.py`, with HTTP-specific code under `streaming/transports/http.py`.
- [ ] `stream=false` still uses the blocking synthesis path and does not depend on streaming-only primitives.
- [ ] `stream=true + response_format=pcm` still works end-to-end through the new subsystem with `StreamingConfig` injected by app creation rather than hardcoded route constants.

## Production-ready criteria

- [ ] Contract tests prove the OpenAI-compatible stream route is wired through the subsystem.
- [ ] Existing non-streaming OpenAI speech tests still pass.
- [ ] No raw user text is logged from the streaming route.

## Blocked by

- `01-create-streaming-package-and-core-pipeline.md`
