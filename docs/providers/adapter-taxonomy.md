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

## Checklist

1. Catalog entry declares provider family, engine ID, payload template, file roles, license, and locale.
2. Install hydration produces a `VoiceDescriptor` without route-specific provider branches.
3. Fake lifecycle tests cover at least `preset/shared-artifact` and `model-file` providers.
4. Reference/zero-shot and dialogue families remain gated/deferred unless governance or
   single-speaker semantics are implemented in an ADR.
