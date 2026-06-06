# Add Piper and Kokoro ProviderInstaller adapters

Status: planned

## Parent

ADR-0028 — `docs/adr/ADR-0028-tiered-provider-installer.md`

## What to build

Add initial ProviderInstaller adapters for Piper-plus and Kokoro that can check runtime availability and explain automatic/guided/external setup capability for the current packaging phase.

## Acceptance criteria

- [ ] Piper installer reports provider status using the generic ProviderInstaller protocol.
- [ ] Kokoro installer reports provider status using the generic ProviderInstaller protocol.
- [ ] Install mode is honest for the current packaging target and does not claim automatic install unless implemented.
- [ ] Runtime check results feed voice pack readiness and setup recommendations.

## Production-ready criteria

- [ ] Tests cover provider installed, missing dependency, broken import, unsupported platform, and user-safe explanation.
- [ ] CLI/API can show provider runtime status for Piper and Kokoro.
- [ ] Docs describe current install mode limitations and future automatic install path.

## Blocked by

- ADR-0028 issue 01-define-provider-installer-protocol
