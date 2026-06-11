# Unsupported format or locale

Use this topic when synthesis fails with an unsupported audio format or locale mismatch.

1. Request `pcm` or `wav` from core synthesis.
2. Treat `mp3`, `ogg`, `aac`, and `opus` as optional provider or export capabilities, not core guarantees.
3. Choose a voice whose supported locales include the requested BCP-47 locale.

Mery does not silently fallback to another format or locale after this error.
