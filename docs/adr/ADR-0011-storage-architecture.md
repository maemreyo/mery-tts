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
- **$HOME-relative fixed paths** — always use `~/mery/`. Not following OS
  conventions; conflicts with multi-user setups; not relocatable.
- **Platform app data via `platformdirs`** — use the OS-correct app data
  directory by default. Follows conventions on macOS, Linux, and Windows.
- **Fully user-configurable** — require the user to specify every path.
  Too much setup friction for Phase 1 users.

## Decision

Use **platformdirs-resolved default storage** with an **advanced user override for the
model directory**, managed exclusively through the helper's CLI and config file.

Default storage roots:
- macOS: `~/Library/Application Support/Mery TTS/`
- Linux: `~/.local/share/Mery TTS/`
- Windows: `%APPDATA%\Mery TTS\`

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
  last-doctor.json    # result of most recent mery doctor run
```

Users who need models on a different disk can run `mery storage move --to <dir>`.
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
- `mery storage show|move|repair` centralises storage management in the CLI rather
  than exposing filesystem concerns to Zam Reader.
- Low-disk diagnostics are emitted through the structured error taxonomy (ADR-0010)
  so Zam Reader can surface them without knowing the filesystem layout.

## Consequences

**Enables:**
- Same code path under `uv tool install`, PyInstaller, and signed installer (ADR-0008).
- Tests use `tmp_path` fixtures; no real `~/Library/...` path is ever touched in CI.
- `mery storage show` gives users a one-command disk-usage summary.
- `mery storage move` migrates models without re-downloading.
- `mery storage repair` cleans partial downloads and re-verifies the model store.

**Constrains:**
- `settings/config.py` is a hard prerequisite; every module that needs a path calls
  `HelperSettings` — no module may construct storage paths independently.
- Model deletion uses `modelId` only; raw paths are never passed through the API.
- `modelDirOverride` applies only to the `models/` subtree; config, logs, cache, and
  diagnostics always remain under the platformdirs root.
- Storage migration (`storage move`) must be atomic enough that a crash leaves the
  helper in a consistent state (old directory intact or new directory complete).

## Amendment — artifact and voice identity split

**Date:** 2026-06-05  
**Source:** Grill 03, Q34–Q38; ADR-0015/ADR-0016

Installed storage uses two identity axes:

```text
artifactId -> stored bytes/package identity
voiceId    -> installed/routable voice identity
```

Artifacts and voices are stored separately:

```text
artifacts/{engineId}/{artifactId}/artifact.json
voices/{safeVoiceId}.json
```

A single artifact may be referenced by multiple installed voices, and one voice may reference multiple artifacts. Artifact garbage collection removes only artifacts with zero live voice-manifest references. Installed voice manifests persist logical artifact references and payload templates; runtime paths are hydrated by `VoiceRegistry.refresh()`.

## Related

- ADR-0003 (Python runtime — `platformdirs` in dependencies)
- ADR-0008 (packaging — packaging-agnostic path requirement)
- ADR-0006 (security — `config.json` file permissions)
- ADR-0007 (catalog integrity — bundled catalog path, model store path)
- ADR-0015 (catalog model: normalized internal, flat external, artifact/voice identity)
- ADR-0016 (install job lifecycle)
- `docs/codebase/FOLDER_STRUCTURE.md` → storage layout section
- `docs/integration/zam-reader-readiness-contract.md` §9
