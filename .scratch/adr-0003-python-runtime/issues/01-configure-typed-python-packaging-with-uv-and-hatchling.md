# Configure typed Python packaging with uv and hatchling

Status: completed

## Parent

ADR-0003 — `docs/adr/ADR-0003-python-runtime.md`

## What to build

Configure the helper as a Python 3.12+ `src/` layout package managed by `uv` and built with hatchling, including a typed marker and importable package metadata.

## Acceptance criteria

- [ ] Project metadata declares Python 3.12+ and hatchling build backend.
- [ ] Source lives under a PEP 518 `src/` layout with package name `mery_tts`.
- [ ] The package includes `py.typed` and exposes minimal version metadata.
- [ ] `uv sync` installs development dependencies without requiring engine extras by default.

## Blocked by

None - can start immediately

## Comments
