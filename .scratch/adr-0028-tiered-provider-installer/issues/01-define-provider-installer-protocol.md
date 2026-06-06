# Define ProviderInstaller protocol

Status: completed

## Parent

ADR-0028 — `docs/adr/ADR-0028-tiered-provider-installer.md`

## What to build

Define the ProviderInstaller port and provider runtime status model so Mery can reason about automatic, guided, and external provider runtime setup without hardcoding provider behavior in routes or clients.

## Acceptance criteria

- [x] ProviderInstaller exposes check, install, repair, and explain operations.
- [x] Provider runtime status includes provider ID, install mode, status, reason, recommended action, and user-safe explanation.
- [x] Install modes include automatic, guided, and external.
- [x] Provider status can be serialized through API/CLI without leaking unsafe paths or tracebacks.

## Production-ready criteria

- [x] Unit tests cover status serialization, unsupported platform, missing runtime, installed runtime, broken runtime, and repair recommendation.
- [x] Type contracts prevent provider-specific payloads from leaking into generic setup services.
- [x] Docs identify ProviderInstaller as a port, not a Piper/Kokoro implementation detail.

## Blocked by

- None - can start immediately
