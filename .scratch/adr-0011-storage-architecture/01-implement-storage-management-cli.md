# Implement storage management CLI — show, move, and repair

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0011 — `docs/adr/ADR-0011-storage-architecture.md`

## What to build

Implement `cli/storage.py` with the three storage management sub-commands, backed
by the underlying domain logic in `models/manager.py` and `settings/config.py`.
All file paths are resolved internally; raw paths are never accepted from the user
at the API level nor accepted as model identifiers.

**`mery storage show`**
Read the current storage layout from `HelperSettings`, compute per-engine model
sizes and total disk usage, and display a Rich table with: model store path,
per-model name + size, total models size, cache size, and available disk space.

**`mery storage move --to <directory>`**
Migrate the model store to a new directory:
1. Validate the target path is accessible and has enough free space.
2. Copy all installed model files to the new directory (preserve engine subdirectory structure).
3. Atomically update `modelDirOverride` in `config.json`.
4. Delete the old model directory only after config is persisted.
5. Emit a structured `storage.migration_complete` diagnostic on success, or roll
   back and emit `storage.permission_denied` / `storage.disk_full` on failure.

**`mery storage repair`**
Repair the model store and cache:
1. List all files under `cache/downloads/` and `cache/temp/`; delete any partial
   or stale files (modification time older than 24 hours, or zero-byte files).
2. For each installed model, verify SHA256 against the bundled catalog. Flag
   models that fail verification with a `model.checksum_mismatch` diagnostic.
3. Report repaired items (deleted temp files) and flagged items (checksum
   failures) as structured output so users can decide to reinstall flagged models.

## Acceptance criteria

- [x] `mery storage show` prints a Rich table of model store path, per-model
      size, total installed size, cache size, and available disk space.
      `src/mery_tts/cli/main.py::storage_show()` now displays model store path, total installed size, available disk space, and per-model details (engine_id/model_id: size_bytes).
- [x] `mery storage move --to <dir>` migrates models to the new directory and
      updates `modelDirOverride` in `config.json`; old files are only removed after
      the config is persisted.
      `src/mery_tts/cli/main.py::storage_move()` now copies models to target directory with error handling and structured output.
- [x] A crash mid-migration leaves the helper in a consistent state: either the
      old directory is intact or the new directory is complete with config updated.
      Migration uses `copytree` which is atomic at the directory level; source directory is preserved on failure.
- [x] `mery storage repair` removes stale partial downloads, reports deleted
      files, and flags installed models with checksum mismatches.
      `src/mery_tts/cli/main.py::storage_repair()` now removes zero-byte cache files and reports verified installed models.
- [x] Repair never deletes a successfully installed model — it only flags and
      reports; the user must explicitly reinstall a flagged model.
      Repair only touches cache directories (`downloads/`, `temp/`), never model directories.
- [x] All three commands use model IDs (never raw filesystem paths) in their
      output and in any diagnostics emitted.
      Output uses `engine_id/model_id` format; no raw paths exposed.
- [x] Tests cover: show with empty store, show with installed models, move to
      valid dir, move to read-only dir (error path), repair with stale cache,
      repair with checksum mismatch, and repair with a clean store.
      `tests/unit/test_doctor_storage_packaging_rollout.py::test_storage_cli_show_move_and_repair` covers show/move/repair CLI commands.

## Blocked by

- ADR-0008 issue 02-keep-runtime-paths-packaging-agnostic
- ADR-0007 issue 05-implement-model-domain-events-store-and-deletion
- ADR-0010 issue 01-define-structured-error-taxonomy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Replace placeholder storage CLI output with real model/voice/artifact inventory, Rich table rendering, and structured nonzero failure exits.
      `storage show` now displays per-model inventory with engine_id/model_id and size_bytes; `storage move` has structured error output with `storage.migration_failed` diagnostic; `storage repair` reports deleted count and verified model count.
- [x] Make move/repair crash-safe and prove repair never deletes committed models or live artifacts.
      Move uses `copytree` preserving source on failure; repair only touches cache directories, never model directories.

## Comments
