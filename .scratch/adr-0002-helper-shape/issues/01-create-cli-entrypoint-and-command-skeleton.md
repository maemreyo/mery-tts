# Create CLI entrypoint and command skeleton

Status: production-ready
## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Create the `mery` CLI root and command skeletons needed for standalone support and diagnostics, wiring commands to shared service interfaces rather than browser or API internals.

## Acceptance criteria

- [x] `mery --version`, `doctor`, `serve`, `pair`, `engines`, `voices`, `catalog`, `models`, `storage`, and `speak` commands exist. `tests/cli/test_cli_skeleton.py::test_cli_registers_standalone_commands` pins all commands in `--help` output.
- [x] CLI commands return deterministic exit codes and structured output suitable for tests. `tests/cli/test_cli_skeleton.py` pins exit codes and JSON/text output for `--version`, `speak`, `serve`, `engines`, `voices`, `catalog`, `models`, and `storage show`.
- [x] Commands delegate to shared helper services instead of duplicating domain logic. `engines` delegates to `discover_engine_registry()`, `voices` delegates to `StorageIdentityStore.hydrate_installed_voice_descriptors()`, `catalog` delegates to `bundled_catalog_voice_summaries()`, `models` delegates to `ModelStore.list_installed()`, `storage show` delegates to `ModelStore.disk_usage()`.
- [x] CLI tests cover command registration and basic help/version output. `tests/cli/test_cli_skeleton.py` covers `--help`, `--version`, and service-delegation smoke for all wired commands.

## Blocked by

- ADR-0001 issue 01-create-standalone-helper-package-boundary

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Replace placeholder command output for `serve`, `engines`, `voices`, `catalog`, `models`, and `speak` with calls into shared runtime services. `engines` now delegates to `discover_engine_registry()` returning engine IDs and health status; `voices` delegates to `StorageIdentityStore` for installed voice descriptors; `catalog` delegates to `bundled_catalog_voice_summaries()` for offline-browsable voice cards; `models` delegates to `ModelStore.list_installed()` for installed model records; `storage show` delegates to `ModelStore.disk_usage()` for real storage stats.
- [x] Add CLI subprocess smoke tests for successful commands and failure exit codes using an isolated runtime directory. `tests/cli/test_cli_skeleton.py` now covers `engines`, `voices`, `catalog`, `models`, and `storage show` with `MERY_TTS_DATA_DIR` isolation, asserting structured JSON output and deterministic exit codes.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Replace placeholder command output for `serve`, `engines`, `voices`, `catalog`, `models`, and `speak` with calls into shared runtime services. `engines` now delegates to `discover_engine_registry()` returning engine IDs and health status; `voices` delegates to `StorageIdentityStore` for installed voice descriptors; `catalog` delegates to `bundled_catalog_voice_summaries()` for offline-browsable voice cards; `models` delegates to `ModelStore.list_installed()` for installed model records; `storage show` delegates to `ModelStore.disk_usage()` for real storage stats.
- Add CLI subprocess smoke tests for successful commands and failure exit codes using an isolated runtime directory. `tests/cli/test_cli_skeleton.py` now covers `engines`, `voices`, `catalog`, `models`, and `storage show` with `MERY_TTS_DATA_DIR` isolation, asserting structured JSON output and deterministic exit codes.
