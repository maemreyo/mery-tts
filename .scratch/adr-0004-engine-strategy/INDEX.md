# ADR-0004 — Dual-engine from day one

Source ADR: `docs/adr/ADR-0004-engine-strategy.md`

## Goal

Implement a genuinely modular dual-engine architecture with `piper-plus` and `kokoro` behind the same `EngineAdapter` contract, discovered through Python entry points.

## Issues

1. [Define EngineAdapter and EngineRegistry discovery](issues/01-define-engine-adapter-and-engine-registry-discovery.md)
2. [Implement VoiceRegistry routing and refresh semantics](issues/02-implement-voice-registry-routing-and-refresh-semantics.md)
3. [Implement Piper-plus adapter contract](issues/03-implement-piper-plus-adapter-contract.md)
4. [Implement Kokoro adapter contract](issues/04-implement-kokoro-adapter-contract.md)
