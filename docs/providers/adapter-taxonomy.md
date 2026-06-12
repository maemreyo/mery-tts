# Provider adapter taxonomy

Mery provider adapters must fit one approved family and expose behavior through
`EngineAdapter`, `VoiceDescriptor`, catalog entries, and storage hydration. Provider-specific
logic must not enter API routes, install job state machines, core storage layout, or web-console
feature logic.

## Families

- `preset/shared-artifact`: a shared model artifact exposes named preset voices.
- `model-file`: each voice resolves to one installed model file.
- `embedding/vc`: voices hydrate embedding or voice-conversion payloads from artifacts.
- `reference`: reference/zero-shot voices are gated/deferred until governance is explicit.
- `designed`: parameter-designed voices use an explicit designed payload contract.
- `dialogue`: dialogue/multi-speaker providers are gated/deferred until single-speaker semantics are explicit.

## ADR-0049 admission tiers

Provider family describes adapter shape. Admission tier describes product visibility.
A provider cannot appear in the default User Mode catalog or install wizard until it has a
complete scorecard, passes all fit gates, passes package-install provider e2e, and records
support-bundle evidence.

- **Tier A — Appliance baseline:** CPU-friendly, reliable, simple install, suitable for
  long-form reading and basic local assistant use.
- **Tier B — Modern high-quality local:** higher-quality local providers that still pass
  local-fit, appliance-fit, quality-fit, and modern-fit. P2 provider work targets Tier B.
- **Tier C — Specialist/governance-gated:** reference audio, voice cloning, dialogue,
  multi-speaker, emotional, or misuse-sensitive providers. These require separate consent,
  provenance, privacy, storage/audit, warning, and licensing governance before user exposure.
- **Tier D — Research/unsupported:** interesting projects for maintainer notes only.

Experimental providers may appear only in Developer Mode or docs with explicit badges such as
`experimental`, `not appliance-ready`, `manual setup`, `not supported by wizard`, and
`package e2e may fail`. They must not be offered by the default User Mode catalog or guided
install wizard.

## Checklist

1. Catalog entry declares provider family, engine ID, payload template, file roles, license, and locale.
2. Install hydration produces a `VoiceDescriptor` without route-specific provider branches.
3. Fake lifecycle tests cover at least `preset/shared-artifact` and `model-file` providers.
4. Provider scorecard covers local-fit, appliance-fit, quality-fit, modern-fit, license/provenance,
   model size, hardware envelope, install complexity, API/CLI stability, testability, UX risk,
   privacy/security risk, and blockers.
5. Package-install provider e2e proves dependency detection, model install, synthesis, status,
   delete cleanup, and sanitized support-bundle evidence before default catalog exposure.
6. Reference/zero-shot and dialogue families remain gated/deferred unless governance or
   single-speaker semantics are implemented in an ADR.
