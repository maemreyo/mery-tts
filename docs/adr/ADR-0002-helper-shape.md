# ADR-0002 — Helper shape: CLI + daemon hybrid

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 2

## Context

The helper needs to serve two audiences: developers/CLI users who want to test
and debug, and Zam Reader which needs a long-running low-latency API.

## Decision

Build a **hybrid helper**: one Python package that exposes both a `zam-tts` CLI
and a daemon/server mode via `zam-tts serve`.

## Rationale

- CLI-first enables standalone testing, QA, and support without a browser.
- Daemon mode enables warm model loading, streaming synthesis, WebSocket events,
  and the low-latency UX Zam Reader needs.
- A hybrid avoids shipping two separate packages and keeps model management,
  catalog, and diagnostics in a single place.
- `zam-tts doctor` and `zam-tts speak --play` are critical for user support: they
  let users verify the helper works before touching Zam Reader settings.

## Consequences

**Enables:**
- `zam-tts doctor` is a self-contained diagnostic that works with zero Zam Reader.
- CLI tests can run in CI without a real browser or extension.
- The same engine adapters serve both CLI playback and WS streaming.

**Constrains:**
- The audio output module must be split: `audio/player.py` (CLI sounddevice) and
  `audio/encoder.py` (WS PCM16 streaming). They share the same PCM data contract
  but use different sinks.
- Server mode and CLI mode share `EngineRegistry`; the registry must be safely
  instantiated in both contexts.

## Related

- ADR-0003 (Python runtime)
- ADR-0005 (API protocol)
- `docs/FOLDER_STRUCTURE.md` → `cli/` and `api/` modules
