# Define ProviderInstaller protocol

Status: planned

## Parent

ADR-0028 — `docs/adr/ADR-0028-tiered-provider-installer.md`

## What to build

Define the ProviderInstaller port and provider runtime status model so Mery can reason about automatic, guided, and external provider runtime setup without hardcoding provider behavior in routes or clients.

## Acceptance criteria

- [ ] ProviderInstaller exposes check, install, repair, and explain operations.
- [ ] Provider runtime status includes provider ID, install mode, status, reason, recommended action, and user-safe explanation.
- [ ] Install modes include automatic, guided, and external.
- [ ] Provider status can be serialized through API/CLI without leaking unsafe paths or tracebacks.

## Production-ready criteria

- [ ] Unit tests cover status serialization, unsupported platform, missing runtime, installed runtime, broken runtime, and repair recommendation.
- [ ] Type contracts prevent provider-specific payloads from leaking into generic setup services.
- [ ] Docs identify ProviderInstaller as a port, not a Piper/Kokoro implementation detail.

## Blocked by

- None - can start immediately
