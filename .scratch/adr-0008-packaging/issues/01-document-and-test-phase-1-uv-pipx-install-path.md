# Document and test Phase 1 uv pipx install path

Status: ready-for-agent

## Parent

ADR-0008 — `docs/adr/ADR-0008-packaging.md`

## What to build

Make the Phase 1 developer/early-adopter install path reliable and documented for `uv tool install` and `pipx install`, including CLI entrypoint availability and first-run commands.

## Acceptance criteria

- [ ] README or setup docs explain `uv` and `pipx` install paths and first-run commands.
- [ ] Package metadata exposes the `zam-tts` CLI after installation.
- [ ] CI or smoke tests verify install-equivalent behavior, CLI entrypoint, server startup, and teardown.
- [ ] Docs clearly label Phase 1 as early access requiring Terminal.

## Blocked by

- ADR-0002 issue 01-create-cli-entrypoint-and-command-skeleton
- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Comments
