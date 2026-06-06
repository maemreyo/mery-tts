# Introduce InstalledVoiceResolver

Status: planned

## Parent

ADR-0024 — `docs/adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`

## What to build

Introduce an `InstalledVoiceResolver` that converts manifest-level `VoiceDescriptor` records into resolved read-only voice payloads with validated absolute paths for engine adapters.

## Acceptance criteria

- [ ] `VoiceRegistry` remains lightweight and stores no absolute paths or runtime objects.
- [ ] Resolver validates safe relative paths from voice manifests under known artifact roots.
- [ ] Resolver returns immutable resolved voice objects for model-file and preset/shared-artifact payloads.
- [ ] Resolver rejects traversal, missing artifacts, missing files, ambiguous artifacts, and unsupported payload families.

## Production-ready criteria

- [ ] Unit tests cover valid Piper and Kokoro resolved payloads using temp directories.
- [ ] Security tests prove absolute/Windows/traversal paths cannot escape artifact roots.
- [ ] Adapters receive resolved paths only through the resolver layer, never from `RuntimePaths` directly.

## Blocked by

- None - can start immediately
