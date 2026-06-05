# Isolate engine dependencies as optional extras

Status: completed

## Parent

ADR-0003 — `docs/adr/ADR-0003-python-runtime.md`

## What to build

Move engine-specific dependencies behind optional extras so a broken or missing Kokoro install cannot break Piper-plus, the helper core, CLI diagnostics, or contract tests.

## Acceptance criteria

- [ ] Engine packages are declared as optional extras rather than required core dependencies.
- [ ] The default install can run helper core tests and CLI diagnostics without real engine packages.
- [ ] Installing all extras enables both first-party engine adapters.
- [ ] Tests cover behavior when an optional engine dependency is unavailable.

## Blocked by

- 01-configure-typed-python-packaging-with-uv-and-hatchling

## Comments
