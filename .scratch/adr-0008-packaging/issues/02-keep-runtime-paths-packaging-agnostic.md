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
- [ ] Packaging mode does not change CLI, API, engine, model, catalog, or diagnostics behavior.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Exercise runtime paths under environment overrides with daemon, catalog refresh, model install, logs, config, and doctor outputs.
  - Progress: `tests/unit/test_runtime_paths.py::test_runtime_paths_support_environment_override` proves `MERY_TTS_DATA_DIR` propagates to config, models, cache, logs, and catalog directories; daemon, catalog refresh, model install, log, and doctor-output end-to-end path exercises remain pending.
- [ ] Ensure no package-relative writable paths are used once installed from a wheel/tool environment.
  - Progress: `tests/unit/test_runtime_paths.py::test_runtime_paths_never_use_package_relative_writable_dirs` proves default runtime paths avoid the package/repository root. Clean wheel smoke already proved installed CLI/server startup uses isolated runtime data; a dedicated wheel/tool assertion for every writable path remains pending.

## Comments
