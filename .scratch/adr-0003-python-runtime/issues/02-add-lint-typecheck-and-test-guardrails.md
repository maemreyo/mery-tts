# Add lint typecheck and test guardrails

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0003 — `docs/adr/ADR-0003-python-runtime.md`

## What to build

Add the strict Python quality gates that prevent the helper from becoming loose scripts: ruff lint/format, `mypy --strict`, pytest layout, and task-runner commands.

## Acceptance criteria

- [x] Ruff lint and format checks are configured for source and tests. `pyproject.toml` defines Ruff lint/format config and `Makefile` runs `uv run ruff format --check src tests` plus `uv run ruff check src tests`; `tests/unit/test_project_guardrails.py` pins this contract.
- [x] `mypy --strict` runs against `src/mery_tts`. `pyproject.toml` sets `strict = true` and `files = ["src/mery_tts"]`; `Makefile` runs `uv run mypy src/mery_tts`; `tests/unit/test_project_guardrails.py` pins this contract.
- [x] Pytest has unit/contract/engine/integration/CLI marker conventions. `pyproject.toml` declares `unit`, `contract`, `cli`, `engine`, and `integration` markers; `tests/unit/test_project_guardrails.py` pins the marker declarations and the `tests/unit`, `tests/contract`, and `tests/cli` directory convention.
- [x] Local task commands run lint, typecheck, tests, and a combined check gate. `Makefile` exposes `format-check`, `lint`, `typecheck`, `test`, `smoke`, and combined `check` targets.

## Blocked by

- 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Add a single documented `check` gate that runs lint, format check, strict mypy, tests, and production smoke commands. `make check` runs Ruff format check, Ruff lint, strict mypy, non-engine/non-integration pytest, and CLI smoke commands.
- [x] Keep engine/integration markers separated so CI can run core checks without optional engine downloads but still exposes real-runtime jobs. `.github/workflows/check.yml` runs default core checks through `make check`, which excludes `engine` and `integration` markers, and exposes a separate manual `real-runtime` job for `uv run pytest -m "engine or integration"` with engine extras; `tests/unit/test_project_guardrails.py` pins this CI split.

## Comments
