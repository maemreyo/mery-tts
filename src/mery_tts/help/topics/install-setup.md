# Install and setup recovery

Use this topic when Mery is not installed, the daemon will not start, or setup did not complete.

1. Run `mery doctor` to check paths, token configuration, catalog availability, and installed engines.
2. Run `mery voice-packs list` to inspect bundled voice packs.
3. Start the helper with `mery serve` after setup checks pass; it prints suggested next commands before blocking.

This recovery path is local and does not require internet access unless you explicitly install or refresh remote model artifacts.
