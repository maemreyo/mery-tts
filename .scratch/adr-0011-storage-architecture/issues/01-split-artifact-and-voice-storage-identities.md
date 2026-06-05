# Split artifact and voice storage identities

Status: completed

## Parent

ADR-0011 amendment — `docs/adr/ADR-0011-storage-architecture.md`

## What to build

Update storage implementation and tests so stored bytes are addressed by `artifactId` and routable voices are addressed by `voiceId`. Voice manifests should reference artifact IDs, and runtime paths should be hydrated during registry refresh rather than persisted as brittle absolute paths.

## Acceptance criteria

- [ ] Storage layout supports `artifacts/{engineId}/{artifactId}/artifact.json` and `voices/{safeVoiceId}.json`.
- [ ] Installed voice manifests persist logical `artifactRefs` and payload templates, not absolute runtime paths.
- [ ] Runtime voice descriptors hydrate paths from artifact manifests during `VoiceRegistry.refresh()`.
- [ ] Tests cover one artifact referenced by multiple voices, one voice referencing multiple artifacts, safe voice filename mapping, and missing artifact diagnostics.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Comments
