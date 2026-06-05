# Add diagnostic sanitization and error factories

Status: completed

## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Implement reusable error factories and a fail-closed diagnostic sanitizer so every layer can emit structured errors without leaking raw user text, page URLs, tokens, user identifiers, nested sensitive data, or raw engine messages.

## Acceptance criteria

- [ ] Diagnostic metadata allows only shallow scalar values after sanitization.
- [ ] Forbidden fields such as raw text, article content, page URLs, tokens, API keys, user identifiers, and raw engine messages are removed.
- [ ] If sanitization is uncertain, diagnostic metadata is omitted rather than emitted unsafely.
- [ ] Tests cover allowed metadata, forbidden metadata, nested data, and engine exception translation.

## Blocked by

- 01-define-structured-error-taxonomy

## Comments
