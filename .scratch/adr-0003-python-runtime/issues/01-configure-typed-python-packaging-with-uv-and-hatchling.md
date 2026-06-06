# Configure typed Python packaging with uv and hatchling

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0003 — `docs/adr/ADR-0003-python-runtime.md`

## What to build

Configure the helper as a Python 3.12+ `src/` layout package managed by `uv` and built with hatchling, including a typed marker and importable package metadata.

## Acceptance criteria

- [x] Project metadata declares Python 3.12+ and hatchling build backend. `pyproject.toml` declares `requires-python = ">=3.12"` and `build-backend = "hatchling.build"`; `tests/unit/test_project_guardrails.py` pins both values.
- [x] Source lives under a PEP 518 `src/` layout with package name `mery_tts`. `pyproject.toml` configures Hatchling wheel packages as `["src/mery_tts"]`; `tests/unit/test_project_guardrails.py` pins this package layout.
- [x] The package includes `py.typed` and exposes minimal version metadata. `src/mery_tts/py.typed` exists and package metadata declares `version = "0.1.0"`; `tests/unit/test_project_guardrails.py` pins the typed package marker.
- [x] `uv sync` installs development dependencies without requiring engine extras by default. Engine packages are declared only under optional extras (`piper-plus`, `kokoro`, `all`) and `tests/unit/test_project_guardrails.py::test_engine_dependencies_are_optional_extras_not_default_dependencies` pins that default dependencies exclude `piper-plus` and `kokoro-onnx`.

## Blocked by

None - can start immediately

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Verify wheel/sdist build and install-equivalent CLI execution in a clean environment, not only editable test execution. `uv build` produced `dist/mery_tts_server-0.1.0.tar.gz` and `dist/mery_tts_server-0.1.0-py3-none-any.whl`; a clean temp venv installed the wheel and ran `mery --help`, `mery --version`, and `mery engines` successfully.
- [x] Ensure package data includes bundled catalogs and `py.typed` while excluding caches, scratch files, and local artifacts. Artifact inspection verifies wheel/sdist include `mery_tts/catalog/fixtures/bundled-v1.json`, `mery_tts/py.typed`, `mery_tts/diagnostics/*`, and `mery_tts/models/*`, with no `.scratch`, `__pycache__`, `.mery-tts`, root `models`, root `cache`, root `logs`, or root `diagnostics` entries; `tests/unit/test_project_guardrails.py::test_packaging_runtime_files_are_not_hidden_by_ignore_rules` pins the source ignore/exclusion guardrails.

## Comments
