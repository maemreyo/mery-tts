# Language capability contract

ADR-0048 P1 language support is model-dependent. Mery must not claim that the runtime globally supports every language. User-facing surfaces should describe the locales supported by installed or catalog voices.

## Contract

- Voice metadata uses BCP-47 locale tags such as `en-US` and `vi-VN`.
- `/v1/catalog/voices` and installed voice summaries expose `supported_locales` and `language_support` per voice.
- Launcher readiness exposes `language_support.scope = installed_or_catalog_voice` and the packaged catalog locales.
- The P1 real-audio release gate is the English Piper/Piper-plus baseline voice: `piper-plus.en-us.lessac-low` (`en-US`).
- Vietnamese remains protected through deterministic normalization, segmentation, resolver, and locale-mismatch tests; it is not claimed as a P1 real-audio release gate unless real-runtime evidence exists.

## Safe wording

Use:

> Language support is model-dependent. Choose an installed or catalog voice whose BCP-47 locale matches the text.

Avoid:

- “Mery supports every language.”
- “The runtime supports Vietnamese/English globally.”
- “Any voice can read any language.”

## API fields

Each voice may include:

```json
{
  "supported_locales": ["en-US"],
  "language_support": {
    "scope": "voice",
    "supported_locales": ["en-US"],
    "wording": "Language support is specific to this installed or catalog voice.",
    "p1_audio_gate": true
  }
}
```

`p1_audio_gate` is true only for the P1 baseline voice that has release-smoke evidence requirements.

## Diagnostics

Unsupported locale or voice/locale mismatch must return structured diagnostics and must not include raw synthesis text. Locale diagnostics may include requested and selected BCP-47 locale tags because those are not user text.
