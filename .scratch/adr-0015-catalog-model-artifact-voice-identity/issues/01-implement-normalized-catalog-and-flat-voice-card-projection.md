# Implement normalized catalog and flat voice card projection

Status: completed

## Parent

ADR-0015 — `docs/adr/ADR-0015-catalog-model-artifact-voice-identity.md`

## What to build

Implement the catalog model that separates installable catalog entries, stored artifacts, routable voices, and engine adapters. The slice should load a trusted normalized catalog fixture and expose a flat voice-card API projection that clients can use without understanding the internal graph.

## Acceptance criteria

- [ ] Catalog data is represented internally as engines, artifacts, and voices with distinct `catalogEntryId`, `artifactId`, `voiceId`, and `engineId` identities.
- [ ] `GET /v1/catalog/voices` returns flat voice cards with install identity, voice identity, engine, language, license/commercial-use, size, installed state, and capabilities.
- [ ] Catalog validation rejects missing graph references and duplicate catalog/artifact identities.
- [ ] Tests prove shared-artifact and model-file catalog shapes both project to flat voice cards without exposing raw install URL authority.

## Blocked by

- ADR-0013 issue 01-define-voice-descriptor-payload-union-and-adapter-kind-validation

## Comments
