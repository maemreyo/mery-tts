# Keep runtime paths packaging agnostic

Status: completed

## Parent

ADR-0008 — `docs/adr/ADR-0008-packaging.md`

## What to build

Ensure helper runtime paths use platform app-data locations and never depend on executable-relative paths, so the same internals work under `uv`, `pipx`, standalone bundles, and signed installers.

## Acceptance criteria

- [ ] Settings resolve config, models, cache, logs, and catalog paths via platform-aware app data conventions.
- [ ] No runtime code assumes files are writable relative to the package executable location.
- [ ] Tests cover default paths, environment overrides, and platform-safe path construction.
- [ ] Packaging mode does not change CLI, API, engine, model, catalog, or diagnostics behavior.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Comments
