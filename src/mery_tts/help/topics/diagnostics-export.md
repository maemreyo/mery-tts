# Diagnostics export

Use this topic when support, QA, or an integration partner needs a local evidence bundle.

1. Run `mery doctor` first to capture current health.
2. Generate the sanitized support bundle with either command:
   - `mery diagnostics-export --output <path>/support-bundle.json`
   - `mery launch --action support-bundle --json`
3. Review the exported JSON before sharing it manually outside the machine.

The diagnostics export is standalone and offline. Mery does not upload this bundle, does not enable outbound telemetry, and keeps `/metrics` disabled unless you explicitly opt in locally.

The support bundle is allowed to include version layers, platform summary, provider/runtime health, installed voice summary, catalog/install state, readiness smoke status, recent sanitized diagnostics, and audit counts. It must not include raw input text, bearer tokens, API keys, pairing codes, private URLs, reference audio, audio payloads, private filesystem paths, or model binaries.
