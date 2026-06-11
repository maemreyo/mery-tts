# Provider unavailable

Use this topic when a selected provider is missing, unhealthy, busy, timed out, or disabled by policy.

1. Run `mery doctor --deep --providers <provider-id>` for provider-specific checks.
2. Verify the voice is installed and belongs to an available engine.
3. Retry later for busy or timed-out providers, or select a different installed local voice.

Provider failures should include sanitized diagnostics and must not expose raw synthesis input.
