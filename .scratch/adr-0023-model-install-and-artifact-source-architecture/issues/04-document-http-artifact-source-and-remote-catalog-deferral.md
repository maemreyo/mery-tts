# Document HTTP artifact source and remote catalog deferral

Status: future

## Parent

ADR-0023 — `docs/adr/ADR-0023-model-install-and-artifact-source-architecture.md`

## What to build

Document the deferred remote download path: `HttpArtifactSource`, host allowlisting, retry/resume, progress reporting, signed remote catalog refresh, and network privacy UX.

## Acceptance criteria

- [ ] Future `HttpArtifactSource` requirements include httpx streaming, size/hash verification, allowed hosts, temp files, rollback, and sanitized errors.
- [ ] Remote catalog refresh remains explicit user action and requires signature/trust-tier validation.
- [ ] Progress events and retry/resume behavior are listed as future production-hardening work.
- [ ] Docs explain why bundled artifacts are first milestone and not the final distribution model.

## Production-ready criteria

- [ ] Deferred HTTP/source work has acceptance criteria sufficient for a future AFK implementation agent.
- [ ] Network work is not required by first local usable milestone tests.

## Blocked by

- None - documentation can start immediately
