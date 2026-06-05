# Zam Local TTS Helper Docs

This docs tree is the canonical home for the standalone helper app design.

## Reports

- [`reports/local-tts-helper-design-decisions.md`](reports/local-tts-helper-design-decisions.md) — authoritative decision log for this helper.
- [`reports/local-tts-solutions-research.md`](reports/local-tts-solutions-research.md) — engine and local TTS solution research.
- [`reports/zam-reader-tts-feature-exploration.md`](reports/zam-reader-tts-feature-exploration.md) — copied context on Zam Reader's current Web Speech TTS feature.
- [`reports/zam-reader-audio-grill-followup-decisions.md`](reports/zam-reader-audio-grill-followup-decisions.md) — copied context on Zam Reader audio-session contracts.

## Integration

- [`integration/zam-reader-readiness-contract.md`](integration/zam-reader-readiness-contract.md) — requirements before Zam Reader may use the helper.

## Ownership rule

This helper owns runtime, engines, models, catalogs, local API, diagnostics, and packaging. Zam Reader owns extension UI, provider registry integration, fallback, and bridge client behavior.
