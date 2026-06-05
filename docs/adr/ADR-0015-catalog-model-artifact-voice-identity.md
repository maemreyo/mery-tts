# ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 01, Q5–Q6; Grill 03, Q29–Q31, Q34, Q38

## Context

Mery needs a catalog that can scale from simple one-model-per-voice providers to shared-artifact providers, multi-artifact providers, and future voice cloning or voice-design workflows. Clients need a simple list of installable voices, but the backend needs enough structure to dedupe artifacts, verify downloads, and hydrate runtime voice descriptors.

## Decision

Use a normalized internal catalog graph:

```text
CatalogDocument
  engines[]
  artifacts[]
  voices[]
```

Expose a flat external projection:

```text
GET /v1/catalog/voices -> CatalogVoiceCard[]
```

Keep four identities distinct:

```text
catalogEntryId -> installable catalog item identity
artifactId     -> stored bytes/package identity
voiceId        -> installed/routable voice identity
engineId       -> adapter identity
```

`POST /v1/models/install` accepts only `catalogEntryId`; clients never install by raw URL, raw `voiceId`, or `artifactId`.

Installed voice manifests persist logical references:

```text
voiceId + engineId + artifactRefs[] + payloadTemplate
```

`VoiceRegistry.refresh()` hydrates runtime `VoiceDescriptor` payloads from `VoiceStore` and `ArtifactStore`, resolving current local paths at runtime rather than persisting brittle absolute paths.

Bundled catalog trust derives from package distribution and needs schema/graph validation. Remote catalogs must pass signature, schema, freshness, and allowlist checks before use.

## Rationale

- Normalized internal graph supports shared artifacts and multi-artifact voices.
- Flat API cards keep clients simple and stable.
- `catalogEntryId` install authority prevents raw URL bypasses.
- Artifact/voice identity split makes deletion and GC safe.
- Logical payload templates make installed manifests portable across storage layout changes.

## Consequences

**Enables:** shared artifact deduplication, safe catalog install, storage migration, and provider-family hydration.

**Constrains:** all install flows must go through catalog resolution and trust validation. Direct URL installation is explicitly out of scope.

## Related

- ADR-0007 — Signed catalog + per-file checksums + download allowlist
- ADR-0011 — Helper-owned app storage with platformdirs and user override
- ADR-0013 — VoiceDescriptor discriminated union
- ADR-0016 — Install job lifecycle
- `docs/grills/openai-comp/03-catalog-install-hardening.md`
