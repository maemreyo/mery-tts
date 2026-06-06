# Plan installs from VoicePack graph

Status: planned

## Parent

ADR-0027 — `docs/adr/ADR-0027-voice-pack-install-graph.md`

## What to build

Move install planning from raw model ID inference to VoicePack graph resolution so each install resolves provider runtime checks, artifact copies/downloads, voice manifests, and smoke targets deterministically.

## Acceptance criteria

- [ ] VoicePack install resolves required provider runtimes before artifact install begins.
- [ ] Install plan includes artifact install steps, voice manifest writes, and post-install smoke targets.
- [ ] Shared artifacts are installed once and reused across voices.
- [ ] Invalid graph relationships fail before any filesystem mutation.

## Production-ready criteria

- [ ] Unit tests cover planning for Piper model-file voice, Kokoro preset voice, shared artifacts, and missing dependencies.
- [ ] Existing `/v1/models/install` can delegate through a compatibility adapter or has a documented migration path.
- [ ] Install plan output is deterministic for the same catalog graph.

## Blocked by

- ADR-0027 issue 01-add-voice-pack-graph-schema
