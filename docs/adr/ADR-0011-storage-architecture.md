# ADR-0011 — Helper-owned app storage with platformdirs and user override

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 13

## Context

The helper downloads model files (38–350 MB) and writes runtime config, catalog
cache, logs, and diagnostic output. The question is where these files live and
whether users have control over storage location.

Options considered:
- **Package-relative paths** — hardcode paths relative to the installed package.
  Breaks when packaging method changes (pipx, PyInstaller, signed installer).
- **$HOME-relative fixed paths** — always use `~/zam-tts/`. Not following OS
  conventions; conflicts with multi-user setups; not relocatable.
- **Platform app data via `platformdirs`** — use the OS-correct app data
  directory by default. Follows conventions on macOS, Linux, and Windows.
- **Fully user-configurable** — require the user to specify every path.
  Too much setup friction for Phase 1 users.

## Decision

Use **platformdirs-resolved default storage** with an **advanced user override for the
model directory**, managed exclusively through the helper's CLI and config file.

Default storage roots:
- macOS: `~/Library/Application Support/Zam Local TTS/`
- Linux: `~/.local/share/Zam Local TTS/`
- Windows: `%APPDATA%\Zam Local TTS\`

Layout under the storage root:
```text
config.json          # port, token, allowed origins, modelDirOverride
catalog/
  bundled-catalog.json
  remote-catalog.json
models/
  piper-plus/
  kokoro/
cache/
  downloads/          # in-progress download temp files
  temp/               # atomic install staging area
logs/
  helper.log          # rotating JSON logs (structlog)
diagnostics/
  last-doctor.json    # result of most recent zam-tts doctor run
```

Users who need models on a different disk can run `zam-tts storage move --to <dir>`.
The override is persisted in `config.json` (`modelDirOverride`); the rest of the
layout remains under the platformdirs root.

**Hard rule:** Zam Reader never receives or sends raw filesystem paths. The helper
resolves all storage locations internally from `settings/config.py`.

## Rationale

- `platformdirs` is the correct abstraction for cross-platform app data. Hardcoding
  paths breaks the packaging-agnostic requirement from ADR-0008.
- A default that follows OS conventions requires zero configuration from normal
  users while remaining predictable and inspectable.
- The model directory override supports power users with large models on a secondary
  disk without complicating the default UX.
- `zam-tts storage show|move|repair` centralises storage management in the CLI rather
  than exposing filesystem concerns to Zam Reader.
- Low-disk diagnostics are emitted through the structured error taxonomy (ADR-0010)
  so Zam Reader can surface them without knowing the filesystem layout.

## Consequences

**Enables:**
- Same code path under `uv tool install`, PyInstaller, and signed installer (ADR-0008).
- Tests use `tmp_path` fixtures; no real `~/Library/...` path is ever touched in CI.
- `zam-tts storage show` gives users a one-command disk-usage summary.
- `zam-tts storage move` migrates models without re-downloading.
- `zam-tts storage repair` cleans partial downloads and re-verifies the model store.

**Constrains:**
- `settings/config.py` is a hard prerequisite; every module that needs a path calls
  `HelperSettings` — no module may construct storage paths independently.
- Model deletion uses `modelId` only; raw paths are never passed through the API.
- `modelDirOverride` applies only to the `models/` subtree; config, logs, cache, and
  diagnostics always remain under the platformdirs root.
- Storage migration (`storage move`) must be atomic enough that a crash leaves the
  helper in a consistent state (old directory intact or new directory complete).

## Related

- ADR-0003 (Python runtime — `platformdirs` in dependencies)
- ADR-0008 (packaging — packaging-agnostic path requirement)
- ADR-0006 (security — `config.json` file permissions)
- ADR-0007 (catalog integrity — bundled catalog path, model store path)
- `docs/codebase/FOLDER_STRUCTURE.md` → storage layout section
- `docs/integration/zam-reader-readiness-contract.md` §9
