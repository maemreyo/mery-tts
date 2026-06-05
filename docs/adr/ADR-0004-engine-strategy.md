# ADR-0004 — Dual-engine from day one

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 8

## Context

Should the helper ship one engine first to get to MVP faster, or commit to two
engines from day one to force genuinely modular architecture?

## Decision

Ship **at least two TTS engine adapters from the first usable milestone**:
`piper-plus` (lightweight) and `kokoro` (quality).

## Rationale

- Supporting two engines immediately forces the `EngineAdapter` ABC to be
  genuinely abstract instead of pretending to be abstract around one implementation.
- A single-engine "modular" design is just a monolith with a thin wrapper that
  is never actually tested for substitutability.
- `piper-plus` and `kokoro` cover different use cases: lightweight/fast/offline
  (Piper-plus) vs. higher-quality English (Kokoro). This gives Zam Reader a
  meaningful user-facing choice from day one.
- Both engines run on CPU-only, which is the baseline hardware requirement (Apple M2,
  no discrete GPU). Neither requires CUDA.

## Engine positioning

| Engine | Product label | Primary use case |
|---|---|---|
| `piper-plus` | Lightweight local voice | Fast, low-RAM, multilingual, Vietnamese-capable |
| `kokoro` | Quality local voice | More natural English listening |

## Engine selection rules

- `piper-plus` uses `piper-plus[inference]` Python package (MIT license)
- `kokoro` uses `kokoro-onnx` Python package (CPU ONNX backend, no PyTorch/CUDA)
- Both adapters implement `EngineAdapter` ABC identically
- Engine dependencies are `optional-dependencies` in `pyproject.toml`; a broken
  Kokoro install must not break Piper-plus
- Contract tests run against a **fake engine** (PCM sine wave); real engine tests
  are `@pytest.mark.engine` and CI-optional

## Why piper-plus over original piper-tts

| | `piper-plus` | `piper-tts` (original) |
|---|---|---|
| License | **MIT** — safe for redistribution | GPL-3.0 — viral, blocks commercial use |
| espeak-ng | Not required | Required (GPL transitive dep) |
| Maintenance | Active (2026) | Archived October 2025 |
| EN model size | 38 MB | 60 MB |
| P50 latency | 27 ms | 35 ms |
| Vietnamese | `vi_VM_meeting` (60 MB) | Community models |

## Consequences

**Enables:**
- `EngineRegistry` is genuinely tested for substitutability from day one.
- Zam Reader can offer users a meaningful lightweight vs. quality choice.
- Adding a third engine (e.g., `mac-say`, `edge-tts-online`) only requires a new
  subdirectory under `engines/`; no existing code changes.

**Constrains:**
- Both adapters must be fully implemented before the first integration milestone.
- CI must run contract tests against both adapters (with fake engine stubs).
- Documentation must explain the capability differences without exposing engine internals to Zam Reader.

## Related

- ADR-0001 (product boundary)
- ADR-0005 (API protocol — engine descriptors)
- `docs/FOLDER_STRUCTURE.md` → `engines/` module
- `docs/reports/local-tts-solutions-research.md`
