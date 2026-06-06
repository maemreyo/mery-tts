# Document future direct install permissions

Status: planned

## Parent

ADR-0030 — `docs/adr/ADR-0030-zam-reader-guided-setup-handoff.md`

## What to build

Document the future permission model required before clients such as Zam Reader may directly trigger voice pack installs instead of using guided setup handoff.

## Acceptance criteria

- [ ] Docs state that initial Zam Reader integration uses guided setup handoff only.
- [ ] Future direct install requires explicit install permission, setup session identity, local user confirmation, audit record, and cancellable job status.
- [ ] Direct install cannot be triggered silently by a browser extension.
- [ ] Security considerations cover client spoofing, CSRF/CORS, install abuse, large downloads, and consent replay.

## Production-ready criteria

- [ ] Future direct install is captured as deferred work, not implied as implemented.
- [ ] Docs cross-link ADR-0006 security model and ADR-0029 API-first setup orchestration.
- [ ] Human review confirms first milestone does not over-grant client privileges.

## Blocked by

- None - can start immediately
