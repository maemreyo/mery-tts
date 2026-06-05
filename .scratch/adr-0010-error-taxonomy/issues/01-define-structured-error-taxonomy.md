# Define structured error taxonomy

Status: ready-for-agent

## Parent

ADR-0010 — `docs/adr/ADR-0010-error-taxonomy.md`

## What to build

Define the stable `LocalTTSError` shape, categories, severities, recoverability values, recommended actions, fallback policies, machine codes, i18n key fields, request IDs, and timestamps.

## Acceptance criteria

- [ ] Error schemas include code, category, severity, recoverability, user message key, recommended action, fallback policy, sanitized diagnostic, request ID, and timestamp.
- [ ] Categories cover connection, auth, catalog, model, engine, synthesis, playback, storage, and security.
- [ ] Machine codes from the ADR are represented as stable constants or typed values.
- [ ] Snapshot tests prove every declared error shape is stable.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Comments
