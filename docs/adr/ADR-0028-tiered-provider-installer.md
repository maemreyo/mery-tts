# ADR-0028 — Tiered ProviderInstaller strategy

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Setup/install grill, RCM architecture review

## Context

Real local audio requires provider runtimes as well as model artifacts. Piper, Kokoro, and future engines may have different installation requirements: Python extras, native libraries, platform-specific wheels, CPU/GPU constraints, large dependencies, or manually managed external runtimes.

A fully automatic installer would be convenient but unrealistic for every provider and packaging target. A purely manual provider setup would be frustrating and would make Zam Reader onboarding feel broken. The architecture needs a flexible strategy that can support automatic, guided, and external runtime modes without hardcoding provider-specific behavior in routes or clients.

## Decision

Introduce a `ProviderInstaller` port with tiered capability reporting:

```python
class ProviderInstaller(Protocol):
    provider_id: str

    def check(self) -> ProviderRuntimeStatus: ...
    async def install(self) -> ProviderRuntimeInstallResult: ...
    def repair(self) -> ProviderRuntimeRepairPlan: ...
    def explain(self) -> ProviderRuntimeExplanation: ...
```

Each provider declares an install mode:

```text
automatic:
  Mery can install/repair the runtime locally after explicit user consent

guided:
  Mery can detect requirements and guide the user through steps

external:
  Mery can detect and explain, but runtime is owned outside Mery
```

Provider runtime readiness is checked before artifact install and before smoke. Voice Pack installation may proceed only when required provider runtimes are installed or explicitly accepted as externally managed.

## Rationale

- Keeps provider-specific install logic behind provider adapters.
- Avoids hardcoding Piper/Kokoro package steps into CLI, Console, or Zam Reader.
- Supports platform differences and packaging constraints.
- Gives users honest setup messaging and repair actions.
- Makes provider readiness testable through fake installers.

## Production-ready criteria

This ADR is production-ready only when:

- Provider runtime status includes provider ID, install mode, status, reason, recommended action, and user-safe explanation.
- Voice Pack install checks provider runtime requirements before artifact install.
- At least one fake installer supports automatic success/failure tests.
- Piper and Kokoro have initial installer adapters or guided/external explanations.
- API and CLI expose provider runtime status without leaking unsafe paths or raw tracebacks.
- Tests cover automatic success, automatic failure, guided requirements, external runtime, repair recommendation, and unsupported platform.

## Consequences

**Enables:** convenient setup where possible, honest guided setup where necessary, and future provider expansion.

**Constrains:** provider runtime checks must not be hidden inside synthesis calls only; setup must model runtime readiness explicitly.

## Related

- ADR-0004 — Dual-engine from day one
- ADR-0008 — Budget-aware phased packaging
- ADR-0018 — Provider rollout strategy
- ADR-0019 — Provider adapter taxonomy
- ADR-0024 — Installed voice resolution and runtime caching
- ADR-0027 — VoicePack install graph
