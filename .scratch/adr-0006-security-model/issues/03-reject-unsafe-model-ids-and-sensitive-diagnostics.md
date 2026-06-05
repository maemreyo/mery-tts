# Reject unsafe model IDs and sensitive diagnostics

Status: ready-for-agent

## Parent

ADR-0006 — `docs/adr/ADR-0006-security-model.md`

## What to build

Add reusable guards that reject unsafe model identifiers and sanitize security diagnostics so logs and error payloads never contain tokens, user text, page URLs, raw paths, or raw engine messages.

## Acceptance criteria

- [ ] Model IDs containing path traversal, forward slashes, backslashes, or raw paths are rejected before domain work starts.
- [ ] Security events use stable structured metadata without user text or secrets.
- [ ] Diagnostics sanitizer fails closed by omitting uncertain metadata.
- [ ] Tests prove rejected paths and sanitized logs for auth failure, rate limit, and path rejection.

## Blocked by

- ADR-0010 issue 02-add-diagnostic-sanitization-and-error-factories

## Comments
