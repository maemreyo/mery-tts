# Add setup and voice pack application services

Status: planned

## Parent

ADR-0029 — `docs/adr/ADR-0029-api-first-setup-orchestration.md`

## What to build

Introduce API-agnostic application services for setup recommendations and voice pack orchestration so routes, CLI, and Console share one setup engine.

## Acceptance criteria

- [ ] SetupService accepts client/intent context and returns recommended voice packs and provider requirements.
- [ ] VoicePackService lists packs and resolves pack install plans through domain ports.
- [ ] Services do not depend on FastAPI, Typer, or Zam Reader-specific modules.
- [ ] Routes and CLI can call services without duplicating setup logic.

## Production-ready criteria

- [ ] Unit tests cover setup recommendations for no intent, English reading intent, Vietnamese reading intent, missing provider runtime, and already-installed pack.
- [ ] Service errors use structured sanitized domain errors.
- [ ] Docs show service boundaries and forbidden dependencies.

## Blocked by

- ADR-0027 issue 01-add-voice-pack-graph-schema
- ADR-0028 issue 01-define-provider-installer-protocol
