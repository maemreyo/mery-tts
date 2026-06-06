# Create standalone helper package boundary

Status: production-ready
## Parent

ADR-0001 — `docs/adr/ADR-0001-product-boundary.md`

## What to build

Create the initial standalone helper package shape so runtime code can live independently from Zam Reader, with a minimal importable Python package, package metadata, typed marker, and documentation that identifies `/v1` as the only integration boundary.

## Acceptance criteria

- [x] The repository has a Python `src` package for the helper with a minimal public surface and inline type marker. `pyproject.toml` packages `src/mery_tts`, `src/mery_tts/py.typed` exists, and `tests/unit/test_package_boundary.py::test_package_public_surface_is_minimal` pins the public surface to `PUBLIC_API_BOUNDARY` and `__version__`.
- [x] Package metadata identifies the helper as independently installable/testable and does not reference importing Zam Reader code. `pyproject.toml` declares the standalone `mery-tts-server` package and `tests/unit/test_package_boundary.py` pins the `/v1` public API boundary instead of client imports.
- [x] A smoke test proves the helper package imports without requiring Zam Reader, browser APIs, engines, or model files. `tests/unit/test_package_boundary.py::test_package_imports_without_client_or_engine_dependencies` imports `mery_tts` and asserts version/boundary metadata only.
- [x] README or developer docs keep the boundary rule visible: Zam Reader talks through `/v1`, not Python imports. `README.md` documents `/v1` bridge-contract integration and the non-negotiable no-Python-import boundary; package-boundary tests prevent stale runtime-status drift.

## Blocked by

None - can start immediately

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Package/install smoke must prove `mery` can be installed in a clean environment and import/start without Zam Reader, local checkout paths, engines, or model fixtures. A clean temp venv installed `dist/mery_tts_server-0.1.0-py3-none-any.whl`, ran `mery --help`, `mery --version`, `mery engines`, started `mery serve` with isolated `MERY_TTS_DATA_DIR`/`MERY_TTS_PORT`, authenticated against generated config, and received `/v1/health` `{"status":"ok"}` before teardown.
- [x] README status must describe the actual runtime maturity instead of claiming both no runtime implementation and completed runtime behavior. README status says `Early runtime implementation`, lists implemented CLI/API/test/export slices, and keeps real engine audio validation, durable install lifecycle, packaging smoke, and production hardening pending. `tests/unit/test_package_boundary.py::test_readme_status_describes_early_runtime_without_stale_no_runtime_claim` prevents reintroducing the stale `No runtime implementation yet` claim.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Package/install smoke must prove `mery` can be installed in a clean environment and import/start without Zam Reader, local checkout paths, engines, or model fixtures. A clean temp venv installed `dist/mery_tts_server-0.1.0-py3-none-any.whl`, ran `mery --help`, `mery --version`, `mery engines`, started `mery serve` with isolated `MERY_TTS_DATA_DIR`/`MERY_TTS_PORT`, authenticated against generated config, and received `/v1/health` `{"status":"ok"}` before teardown.
- README status must describe the actual runtime maturity instead of claiming both no runtime implementation and completed runtime behavior. README status says `Early runtime implementation`, lists implemented CLI/API/test/export slices, and keeps real engine audio validation, durable install lifecycle, packaging smoke, and production hardening pending. `tests/unit/test_package_boundary.py::test_readme_status_describes_early_runtime_without_stale_no_runtime_claim` prevents reintroducing the stale `No runtime implementation yet` claim.
