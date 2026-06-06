# Split artifact and voice storage identities

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0011 amendment — `docs/adr/ADR-0011-storage-architecture.md`

## What to build

Update storage implementation and tests so stored bytes are addressed by `artifactId` and routable voices are addressed by `voiceId`. Voice manifests should reference artifact IDs, and runtime paths should be hydrated during registry refresh rather than persisted as brittle absolute paths.

## Acceptance criteria

- [x] Storage layout supports `artifacts/{engineId}/{artifactId}/artifact.json` and `voices/{safeVoiceId}.json`.
- [x] Installed voice manifests persist logical `artifactRefs` and payload templates, not absolute runtime paths.
- [x] Runtime voice descriptors hydrate paths from artifact manifests during `VoiceRegistry.refresh()`.
- [x] Tests cover one artifact referenced by multiple voices, one voice referencing multiple artifacts, safe voice filename mapping, and missing artifact diagnostics.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Hydrate runtime `VoiceDescriptor` paths from artifact manifests and validate missing/corrupt artifact references before routing synthesis.
- [x] Prove shared-artifact GC with multiple voices and multi-artifact voices using persisted manifests across restart.

## Comments
