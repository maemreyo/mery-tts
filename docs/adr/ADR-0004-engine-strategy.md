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

## Engine adapter implementation pattern

**Verdict (Grill Q1):** Engine adapters call engine Python libraries directly — **no subprocess**.

- `PiperPlusAdapter` uses `piper_plus.PiperPlus(onnx_path)` Python API
- `KokoroAdapter` uses `kokoro_onnx` Python API
- Each adapter's `model_runner.py` manages **Python object lifecycle**: model loading, warmup, inference thread-pool — not an OS process
- No engine binary is required on `$PATH`; inference is pure Python + ONNX Runtime
- Principle: adapters must be **flexible, scalable, SoC, modular, extensible** — all engine-specific logic is fully contained inside its subdirectory; nothing outside changes when an engine is added

This ensures `uv tool install` (ADR-0008 Phase 1) works without any extra binary install step.

## EngineRegistry discovery pattern

**Verdict (Grill Q2):** `EngineRegistry` uses **entry-point plugin discovery** — not hardcoded imports.

```toml
# pyproject.toml
[project.entry-points."mery_tts.engines"]
piper-plus = "mery_tts.engines.piper_plus.adapter:PiperPlusAdapter"
kokoro     = "mery_tts.engines.kokoro.adapter:KokoroAdapter"
```

```python
# engines/base.py — EngineRegistry startup
from importlib.metadata import entry_points

for ep in entry_points(group="mery_tts.engines"):
    try:
        adapter_cls = ep.load()
        self._register(adapter_cls())
    except Exception:
        logger.warning("engine %s failed to load, skipping", ep.name)
```

Rules:
- `EngineRegistry` **never** imports any adapter class directly
- Adding a new engine = new subdirectory + one entry-point line in `pyproject.toml`
- Third-party engines can self-register from separate packages
- Failed load → logged warning, adapter skipped; registry does not crash

## Engine selection rules

- `piper-plus` uses the `piper-plus` Python package (MIT license)
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

## Amendment — runtime health visibility

**Date:** 2026-06-05  
**Source:** Grill 01, Q4; ADR-0018/ADR-0019

Import-time adapter failures keep the existing policy: the adapter load failure is logged as a warning, the adapter is skipped, and startup continues.

Runtime health failures for adapters that loaded successfully are different. Loaded adapters whose dependencies, model files, or runtime checks fail should remain inspectable through `GET /v1/engines` with `status: degraded` or `status: unavailable` and a safe `status_reason`.

This preserves startup resilience while making runtime health visible to the web console, diagnostics, and clients. Provider-specific health details stay inside the adapter; `/v1/engines` exposes only the stable engine descriptor/capability surface.

## Related

- ADR-0001 (product boundary)
- ADR-0005 (API protocol — engine descriptors)
- ADR-0018 (provider rollout strategy)
- ADR-0019 (provider adapter taxonomy)
- `docs/FOLDER_STRUCTURE.md` → `engines/` module
- `docs/reports/local-tts-solutions-research.md`
