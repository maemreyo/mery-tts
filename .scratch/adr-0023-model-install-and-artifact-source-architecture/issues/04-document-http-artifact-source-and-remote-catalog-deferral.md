# Document HTTP artifact source and remote catalog deferral

Status: completed

## Parent

ADR-0023 — `docs/adr/ADR-0023-model-install-and-artifact-source-architecture.md`

## What to build

Document the deferred remote download path: `HttpArtifactSource`, host allowlisting, retry/resume, progress reporting, signed remote catalog refresh, and network privacy UX.

## Acceptance criteria

- [x] Future `HttpArtifactSource` requirements include httpx streaming, size/hash verification, allowed hosts, temp files, rollback, and sanitized errors.
- [x] Remote catalog refresh remains explicit user action and requires signature/trust-tier validation.
- [x] Progress events and retry/resume behavior are listed as future production-hardening work.
- [x] Docs explain why bundled artifacts are first milestone and not the final distribution model.

## Production-ready criteria

- [x] Deferred HTTP/source work has acceptance criteria sufficient for a future AFK implementation agent.
- [x] Network work is not required by first local usable milestone tests.

## Documentation

This document captures the remote download path that is deferred past the HTTP-first local usable milestone.

### What is deferred

The first milestone uses bundled artifacts shipped with the application. Future releases will support `HttpArtifactSource` for downloading artifacts on demand.

### HttpArtifactSource requirements

Future implementation includes:

- **HTTP streaming** — httpx or similar library for efficient streaming downloads
- **Size and hash verification** — confirm downloaded artifact integrity before use
- **Allowed hosts** — configurable allowlist for trusted download sources
- **Temp files** — safe temporary storage during download with cleanup on failure
- **Rollback** — revert to previous artifact version if verification fails
- **Sanitized errors** — user-friendly error messages without exposing internal URLs

### Remote catalog refresh

The remote catalog is not automatically refreshed. Users must explicitly trigger refresh, and each refresh requires signature or trust-tier validation to prevent supply-chain attacks.

### Progress and retry

Progress events and retry/resume behavior are production-hardening work deferred to future milestones. The first milestone assumes complete bundled artifacts with no network dependency.

### Why bundled first

Bundled artifacts ensure offline availability and eliminate network failure modes for the first milestone. This is not the final distribution model, but it provides a reliable baseline for initial deployment.

## Blocked by

- None - documentation can start immediately
