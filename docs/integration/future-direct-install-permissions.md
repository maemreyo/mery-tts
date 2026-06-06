# Future direct install permissions

**Status:** Deferred (not implemented in first milestone)
**Date:** 2026-06-06
**Related:** ADR-0006, ADR-0029, ADR-0030

## Current state

The first Zam Reader integration milestone uses **guided setup handoff only**.
Zam Reader opens a Mery setup URL, and the user confirms installation inside
Mery Console or CLI. Zam Reader does NOT directly trigger voice pack installs.

## Future direct install model

Direct client-triggered install APIs may be added in a future milestone, but
only with the following safeguards:

### Requirements

1. **Explicit install permission**: Client must have been granted install scope
   during pairing or through a separate permission grant.
2. **Setup session identity**: Each install request must be tied to a setup
   session with a unique session ID, created when the client opens setup.
3. **Local user confirmation**: Even with install permission, the local user
   must confirm each install action through Mery Console or CLI.
4. **Audit record**: All install actions triggered by clients must be logged
   with client identity, session ID, voice pack ID, timestamp, and outcome.
5. **Cancellable job status**: Install jobs triggered by clients must be
   cancellable through the same API, with immediate effect.

### Security considerations

- **Client spoofing**: Client identity in setup URLs must be validated against
  known clients or require registration. Unknown clients get generic treatment.
- **CSRF/CORS**: Direct install endpoints must enforce origin allowlist and
  require Bearer token auth. Setup URLs alone do not grant install privileges.
- **Install abuse**: Rate limiting on install endpoints. Maximum concurrent
  install jobs per client. Download size limits per session.
- **Large downloads**: Client must receive estimated download size before
  confirmation. User must explicitly accept disk impact.
- **Consent replay**: Setup sessions expire. Install permission does not carry
  across sessions. Each session requires fresh confirmation.

### What is NOT allowed

- Browser extensions silently installing provider runtimes or model artifacts
- Install without visible user confirmation in Mery
- Install triggered by automated scripts without explicit permission grant
- Install that bypasses Mery's provider runtime checks or smoke testing

## Migration path

When direct install is implemented:

1. Add `install` scope to pairing flow
2. Add `POST /v1/setup/sessions` to create setup sessions
3. Add `POST /v1/voice-packs/{id}/install` with session ID and confirmation token
4. Add audit logging for all client-triggered installs
5. Add rate limiting and concurrent job limits
6. Document the permission model in the API reference

## Cross-references

- ADR-0006 — Full localhost security model
- ADR-0029 — API-first setup orchestration
- ADR-0030 — Zam Reader guided setup handoff
