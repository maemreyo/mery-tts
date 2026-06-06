# Add VoicePack graph schema

Status: planned

## Parent

ADR-0027 — `docs/adr/ADR-0027-voice-pack-install-graph.md`

## What to build

Add domain schemas for ProviderRuntime, Artifact, Voice, and VoicePack so install planning can stop relying on raw model IDs as the primary abstraction.

## Acceptance criteria

- [ ] Catalog graph can represent provider runtime requirements, artifacts, voices, and voice packs.
- [ ] VoicePack metadata includes display name, description, locale/use-case recommendation, voice IDs, runtime requirements, and artifact requirements.
- [ ] Schema validation rejects dangling relationships, duplicate IDs, and unsafe identifiers.
- [ ] Existing model/catalog IDs remain representable as compatibility aliases.

## Production-ready criteria

- [ ] Unit tests cover valid single-voice pack, multi-voice pack, shared artifact pack, missing provider runtime, and invalid references.
- [ ] Schema docs distinguish user-facing VoicePack from synthesis-time Voice.
- [ ] No schema field exposes absolute local filesystem paths to clients.

## Blocked by

- None - can start immediately
