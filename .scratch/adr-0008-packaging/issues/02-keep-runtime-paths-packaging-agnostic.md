# Keep runtime paths packaging agnostic

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0008 — `docs/adr/ADR-0008-packaging.md`

## What to build

Ensure helper runtime paths use platform app-data locations and never depend on executable-relative paths, so the same internals work under `uv`, `pipx`, standalone bundles, and signed installers.

## Acceptance criteria

- [x] Settings resolve config, models, cache, logs, and catalog paths via platform-aware app data conventions. `RuntimePaths.from_environment()` uses `platformdirs.user_data_dir("Mery TTS", "zaob-dev")` by default and `tests/unit/test_runtime_paths.py` pins config, models, cache, logs, and catalog subdirectories.
- [x] No runtime code assumes files are writable relative to the package executable location. `tests/unit/test_runtime_paths.py::test_runtime_paths_never_use_package_relative_writable_dirs` proves default runtime paths do not use the repository/package root and all writable runtime directories stay under the runtime data root.
- [x] Tests cover default paths, environment overrides, and platform-safe path construction. `tests/unit/test_runtime_paths.py` covers explicit base construction, full `MERY_TTS_DATA_DIR` override propagation, and package-root avoidance.
- [x] Packaging mode does not change CLI, API, engine, model, catalog, or diagnostics behavior.
  - Evidence: `tests/unit/test_runtime_paths.py::test_packaging_mode_preserves_core_runtime_behavior` runs under an isolated `MERY_TTS_DATA_DIR` and proves CLI `engines`, API `/v1/health`, `/v1/engines`, `/v1/catalog/voices`, `/v1/models/{model_id}`, `/v1/diagnostics`, engine discovery, model store, bundled catalog, and persisted diagnostics all continue working without package-relative writable paths. Existing CLI smoke in `make check` (`mery --help`, `mery --version`, `mery engines`) also remains clean.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Exercise runtime paths under environment overrides with daemon, catalog refresh, model install, logs, config, and doctor outputs.
  - Progress: `tests/unit/test_runtime_paths.py::test_runtime_paths_support_environment_override` proves `MERY_TTS_DATA_DIR` propagates to config, models, cache, logs, and catalog directories; `test_runtime_paths_override_propagates_to_all_runtime_components` exercises end-to-end propagation through `HelperConfigStore`, `ModelStore`, `load_bundled_catalog()`, `DoctorEngine`, and `create_app()` under environment override.
- [x] Ensure no package-relative writable paths are used once installed from a wheel/tool environment.
  - Progress: `tests/unit/test_runtime_paths.py::test_runtime_paths_never_use_package_relative_writable_dirs` proves default runtime paths avoid the package/repository root. Clean wheel smoke already proved installed CLI/server startup uses isolated runtime data; all writable paths are under `RuntimePaths.base_dir` which is either `MERY_TTS_DATA_DIR` or `platformdirs.user_data_dir("Mery TTS", "zaob-dev")`.

## Comments
