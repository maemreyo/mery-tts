# Missing optional dependency

Use this topic when an engine reports a missing optional package or native runtime.

1. Run `mery doctor --deep` to identify which provider is unavailable.
2. Install the matching optional extra for the provider you intend to use.
3. Restart `mery serve` after dependency installation.

Mery core remains usable with other installed providers while the missing optional dependency is repaired.
