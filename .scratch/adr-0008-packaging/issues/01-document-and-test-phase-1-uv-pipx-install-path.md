# Document and test Phase 1 uv pipx install path

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0008 — `docs/adr/ADR-0008-packaging.md`

## What to build

Make the Phase 1 developer/early-adopter install path reliable and documented for `uv tool install` and `pipx install`, including CLI entrypoint availability and first-run commands.

## Acceptance criteria

- [x] README or setup docs explain `uv` and `pipx` install paths and first-run commands. README `Quick start — Phase 1 early access` documents `uv tool install`, `pipx install`, `mery doctor`, `mery serve`, `mery pair`, model install, CLI speak, and WAV export commands.
- [x] Package metadata exposes the `mery` CLI after installation. `pyproject.toml` declares `[project.scripts] mery = "mery_tts.cli.main:app"`; a clean wheel install exposed and ran `mery --help`, `mery --version`, and `mery engines`.
- [x] CI or smoke tests verify install-equivalent behavior, CLI entrypoint, server startup, and teardown. Local wheel-equivalent smoke installed `dist/mery_tts_server-0.1.0-py3-none-any.whl` in a clean temp venv, ran CLI entrypoint smoke, started `mery serve` with isolated `MERY_TTS_DATA_DIR`/`MERY_TTS_PORT`, authenticated `/v1/health`, then tore the server down.
- [x] Docs clearly label Phase 1 as early access requiring Terminal. README section `Quick start — Phase 1 early access` states Phase 1 early access requires Terminal.

## Blocked by

- ADR-0002 issue 01-create-cli-entrypoint-and-command-skeleton
- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Run install-equivalent smoke for `uv tool install`/`pipx` semantics or a local wheel equivalent: `mery --version`, `mery serve`, health call, teardown. Clean temp venv wheel smoke ran `mery --version`, started `mery serve`, authenticated `/v1/health` with the generated local token, and tore the process down.
- [x] Update docs to label the exact production readiness state and any optional engine prerequisites for early access. README Phase 1 quickstart states the packaged core starts, serves `/v1`, and supports deterministic CLI/API smoke paths without optional engine downloads, while real Piper-plus or Kokoro audio requires the matching optional engine extra and remains gated by real-runtime validation; `tests/unit/test_doctor_storage_packaging_rollout.py::test_readme_documents_phase_one_uv_and_pipx` pins this copy.

## Comments
