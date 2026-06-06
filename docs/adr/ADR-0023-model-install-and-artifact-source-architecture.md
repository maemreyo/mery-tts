# ADR-0023 — Model install and artifact source architecture

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Grill local-usable, Q11–Q14

## Context

The first local-usable milestone needs real Piper and Kokoro voices installed by explicit user action. The current install route creates durable job records and storage manifests, but it does not fetch/copy artifacts, verify real model files, or complete jobs automatically. Remote catalog/download support is desirable later, but network complexity should not block the local PoC.

The existing catalog code contains both legacy `Catalog` (`models[].files[]`) and a normalized `CatalogGraph` (`engines`, `artifacts`, `voices`, `entries`). The normalized model is a better runtime foundation for shared artifacts, multiple voices, and provider diversity.

## Decision

Install remains an asynchronous job with polling for every source type, including bundled/local artifacts:

```text
POST /v1/models/install
  → { jobId, status }
GET /v1/models/install/{jobId}
  → status/progress/error
```

CLI may provide blocking UX by starting the job and polling until a terminal state:

```bash
mery models install <catalogEntryId>
```

Introduce a small artifact-source abstraction now:

```python
class ArtifactSource(Protocol):
    source_kind: str

    async def fetch(self, artifact: CatalogArtifact, target_dir: Path) -> FetchedArtifact:
        ...
```

Only `BundledArtifactSource` is required for the first milestone. `HttpArtifactSource` is deferred and documented as future work.

Runtime install consumes `CatalogGraph`. Legacy bundled catalog data is adapted into `CatalogGraph` through a compatibility adapter. Public API may keep `models/install` terminology, but internals separate:

```text
CatalogEntry → ArtifactInstallPlan → VoiceInstallPlan → InstalledVoiceManifest
```

An install commits only when voice manifests are written atomically after all required artifacts verify. Partial installs and artifact-only state are not visible as installed voices.

## Rationale

- Keeping async jobs from the start avoids an API migration when remote downloads arrive.
- A bundled artifact source avoids network risk while still exercising the production install pipeline.
- `ArtifactSource` keeps install orchestration independent from package resources, HTTP clients, and future local import sources.
- `CatalogGraph` models real provider complexity better than flat `models[].files[]`.
- Separating catalog entries, artifacts, and voices supports shared Kokoro base artifacts, Piper model/config pairs, and future provider families.

## Production-ready criteria

This ADR is production-ready only when:

- `POST /v1/models/install` creates a durable job and schedules a worker for bundled artifacts.
- Job status transitions through queued/running to completed or failed; no job remains running forever after worker completion.
- `BundledArtifactSource` copies package resources into a temp location and exposes progress/status appropriate for local copy.
- Artifact size/hash/file-role verification runs before atomic install commit.
- Voice manifests are written only after all required artifacts verify.
- `VoiceRegistry.refresh()` runs after committed install/delete through an application service, not directly from routes or stores.
- Legacy bundled catalog data is adapted to `CatalogGraph`; runtime install uses `CatalogGraph` only.
- Deferred `HttpArtifactSource`, retry/resume, signed remote catalog refresh, and progress WebSocket events have explicit future issues.
- CLI `mery models install` and `mery models delete` are covered by tests.

## Consequences

**Enables:** real local install without network dependency, future remote download support without API redesign, and clean artifact/voice lifecycle semantics.

**Constrains:** install code must not special-case bundled files in API routes; source-specific behavior belongs behind `ArtifactSource`.

## Related

- ADR-0007 — Signed catalog + checksums + allowlist
- ADR-0011 — Server-owned storage with platformdirs and user override
- ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity
- ADR-0016 — Install job lifecycle
- ADR-0021 — Local Zam Reader usable milestone
