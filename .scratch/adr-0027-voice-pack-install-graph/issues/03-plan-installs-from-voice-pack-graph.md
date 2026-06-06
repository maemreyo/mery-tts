# Plan installs from VoicePack graph

Status: completed

## Parent

ADR-0027 — `docs/adr/ADR-0027-voice-pack-install-graph.md`

## What to build

Move install planning from raw model ID inference to VoicePack graph resolution so each install resolves provider runtime checks, artifact copies/downloads, voice manifests, and smoke targets deterministically.

## Acceptance criteria

- [x] VoicePack install resolves required provider runtimes before artifact install begins.
- [x] Install plan includes artifact install steps, voice manifest writes, and post-install smoke targets.
- [x] Shared artifacts are installed once and reused across voices.
- [x] Invalid graph relationships fail before any filesystem mutation.

## Production-ready criteria

- [x] Unit tests cover planning for Piper model-file voice, Kokoro preset voice, shared artifacts, and missing dependencies.
- [x] Existing `/v1/models/install` can delegate through a compatibility adapter or has a documented migration path.
- [x] Install plan output is deterministic for the same catalog graph.

## Blocked by

- ADR-0027 issue 01-add-voice-pack-graph-schema
