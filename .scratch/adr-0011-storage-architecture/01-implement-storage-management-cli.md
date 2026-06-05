# Implement storage management CLI — show, move, and repair

Status: ready-for-agent

## Parent

ADR-0011 — `docs/adr/ADR-0011-storage-architecture.md`

## What to build

Implement `cli/storage.py` with the three storage management sub-commands, backed
by the underlying domain logic in `models/manager.py` and `settings/config.py`.
All file paths are resolved internally; raw paths are never accepted from the user
at the API level nor accepted as model identifiers.

**`zam-tts storage show`**
Read the current storage layout from `HelperSettings`, compute per-engine model
sizes and total disk usage, and display a Rich table with: model store path,
per-model name + size, total models size, cache size, and available disk space.

**`zam-tts storage move --to <directory>`**
Migrate the model store to a new directory:
1. Validate the target path is accessible and has enough free space.
2. Copy all installed model files to the new directory (preserve engine subdirectory structure).
3. Atomically update `modelDirOverride` in `config.json`.
4. Delete the old model directory only after config is persisted.
5. Emit a structured `storage.migration_complete` diagnostic on success, or roll
   back and emit `storage.permission_denied` / `storage.disk_full` on failure.

**`zam-tts storage repair`**
Repair the model store and cache:
1. List all files under `cache/downloads/` and `cache/temp/`; delete any partial
   or stale files (modification time older than 24 hours, or zero-byte files).
2. For each installed model, verify SHA256 against the bundled catalog. Flag
   models that fail verification with a `model.checksum_mismatch` diagnostic.
3. Report repaired items (deleted temp files) and flagged items (checksum
   failures) as structured output so users can decide to reinstall flagged models.

## Acceptance criteria

- [ ] `zam-tts storage show` prints a Rich table of model store path, per-model
      size, total installed size, cache size, and available disk space.
- [ ] `zam-tts storage move --to <dir>` migrates models to the new directory and
      updates `modelDirOverride` in `config.json`; old files are only removed after
      the config is persisted.
- [ ] A crash mid-migration leaves the helper in a consistent state: either the
      old directory is intact or the new directory is complete with config updated.
- [ ] `zam-tts storage repair` removes stale partial downloads, reports deleted
      files, and flags installed models with checksum mismatches.
- [ ] Repair never deletes a successfully installed model — it only flags and
      reports; the user must explicitly reinstall a flagged model.
- [ ] All three commands use model IDs (never raw filesystem paths) in their
      output and in any diagnostics emitted.
- [ ] Tests cover: show with empty store, show with installed models, move to
      valid dir, move to read-only dir (error path), repair with stale cache,
      repair with checksum mismatch, and repair with a clean store.

## Blocked by

- ADR-0008 issue 02-keep-runtime-paths-packaging-agnostic
- ADR-0007 issue 05-implement-model-domain-events-store-and-deletion
- ADR-0010 issue 01-define-structured-error-taxonomy

## Comments
