# Zam Local TTS Helper

Standalone local TTS helper app for Zam Reader.

This repo is intentionally separate from `zreader` so the helper can have its own Python runtime, packaging, model management, CI, and release lifecycle. Zam Reader integrates with it only through a versioned local bridge contract.

## Current status

Design/bootstrap docs only. No runtime implementation yet.

## Design sources

- [`docs/reports/local-tts-helper-design-decisions.md`](docs/reports/local-tts-helper-design-decisions.md) — authoritative decision log.
- [`docs/reports/local-tts-solutions-research.md`](docs/reports/local-tts-solutions-research.md) — local TTS engine survey.
- [`docs/integration/zam-reader-readiness-contract.md`](docs/integration/zam-reader-readiness-contract.md) — requirements before Zam Reader may use this helper.

## Target shape

```text
src/zam_tts/
  api/
  bridge_contract/
  engines/
  models/
  catalog/
  audio/
  diagnostics/
  settings/
  cli/
```

## Non-goals

- This helper is not browser-extension code.
- This helper does not live inside Zam Reader's WXT `src/` tree.
- Zam Reader must not import Python/helper internals; it talks through the bridge contract only.
