# Implement ArtifactSource protocol and bundled source

Status: completed

## Parent

ADR-0023 — `docs/adr/ADR-0023-model-install-and-artifact-source-architecture.md`

## What to build

Introduce an `ArtifactSource` protocol and implement `BundledArtifactSource` for package-resource artifacts used by the first local usable milestone.

## Acceptance criteria

- [x] `ArtifactSource` hides whether bytes come from package resources, HTTP, or a future local import.
- [x] `BundledArtifactSource` reads package resources and copies artifacts to a temp target without network access.
- [x] Source selection is driven by catalog artifact metadata, not API route branches.
- [x] Tests can inject a fake source without touching package resources.

## Production-ready criteria

- [x] Source fetch verifies expected artifact IDs and fails safely on missing resources.
- [x] No API route imports package-resource paths or HTTP clients directly.
- [x] Bundled-source tests cover success, missing resource, size mismatch, and checksum mismatch.

## Blocked by

- ADR-0023 issue 01-adapt-legacy-catalog-to-runtime-catalog-graph
