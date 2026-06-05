# Axis 06 — Operations & Observability (HIDDEN)

**Last updated:** 2026-06-05
**Status in roadmap:** **Not listed** — discovered via research
**Why it matters:** Production TTS needs health checks, metrics, GPU management, batching, concurrency, timeout, graceful shutdown, backpressure. Not glamorous, but production-critical.

---

## What this axis covers

Everything that makes Mery production-grade beyond the protocol and engines. Without this axis, Mery is a prototype. With it, Mery is a service.

## Health checks (3 distinct)

| Endpoint | Purpose | Returns |
|---|---|---|
| `GET /health` | Liveness (process running) | 200 if process alive |
| `GET /ready` | Readiness (can serve requests) | 200 if models loaded + GPU available + warmup done |
| `GET /live` | Process liveness, no dependency check | 200 always (use sparingly) |

**Why 3 distinct?**
- Kubernetes-style orchestration uses `liveness` to restart dead pods, `readiness` to route traffic
- `/health` is for users; `/ready` is for orchestrator
- Mery should expose all 3

## Metrics (minimum set)

| Metric | Type | Purpose |
|---|---|---|
| `mery_requests_total` | counter | Total syntheses, success, failure (by engine, voice) |
| `mery_request_duration_seconds` | histogram | P50, P95, P99 synthesis time |
| `mery_first_audio_latency_seconds` | histogram | TTFB (only for streaming) |
| `mery_audio_duration_seconds_total` | counter | Total audio generated (useful for billing) |
| `mery_errors_total` | counter | Error count by error code |
| `mery_active_sessions` | gauge | Current in-flight syntheses |
| `mery_model_load_seconds` | histogram | Cold start time per engine |
| `mery_gpu_memory_bytes` | gauge | GPU memory used |
| `mery_gpu_temperature_celsius` | gauge | Health monitoring |

**Format:** Prometheus-compatible (industry standard, low overhead)
**Library:** `prometheus-client` (Python), or OpenTelemetry

## GPU management

- **Selection:** `CUDA_VISIBLE_DEVICES` env var or first-available policy
- **Memory budget:** reserve N% for system, rest for inference
- **OOM handling:** fallback to smaller model or CPU
- **Multi-GPU:** future, single GPU for MVP
- **Temperature throttling:** monitor + warn

**Reference:** NVIDIA's MPS (Multi-Process Service) for multi-tenant GPU sharing

## Model warmup

- First synthesis is slow (model load + first inference)
- Warmup: run a dummy synthesis at startup
- Pre-warm all installed engines on daemon start
- Configurable: eager (startup), lazy (on first request), or on-demand

## Batching

- **Batched synthesis:** process multiple texts in one request (use case: book chapter)
- **Dynamic batching:** server groups concurrent requests for parallel inference
- **Trade-off:** latency vs throughput
- Mery's choice: dynamic batching for small requests, dedicated for streaming

## Concurrency

- **Per-engine limit:** max N concurrent syntheses per engine (GPU memory bound)
- **Global limit:** max M total concurrent syntheses
- **Queue overflow:** 503 with `Retry-After` header
- **Per-user limit:** rate limits per token (ADR-0006 already has 60/min synthesize, 10/min install)

## Timeout & cancellation

- **Per-request timeout:** 30s default, configurable
- **Client cancellation:** `synthesize.cancel` WS event, engine stops immediately
- **Engine cancellation:** if engine doesn't support cancel, mark session as orphaned and ignore future writes
- **Graceful degradation:** if engine can't cancel mid-stream, at least stop streaming

## Graceful shutdown

```
SIGTERM received
  → Stop accepting new connections
  → Send WS `helper.statusChanged` event (status=shutting_down)
  → Wait up to N seconds for in-flight to complete
  → Force-cancel remaining
  → Close all WebSockets with code 1001
  → Exit
```

## Streaming backpressure

When client is slow, server should:
- Detect slow consumer (e.g., TCP buffer not draining)
- Drop audio chunks (mark with `dropped: true` metadata)
- OR pause engine inference (engine-side backpressure)
- OR close connection (force client reconnect)

**Mery choice:** pause engine inference, drop chunks beyond buffer size.

## Failure modes (9 catalogued)

| Failure | Cause | Detection | Recovery |
|---|---|---|---|
| **Voice not found** | Invalid voice_id | 404 response | Return valid voice list |
| **Text too long** | Exceeds limit | 413 response | Chunk or reject (configurable) |
| **Invalid characters** | Malformed input | 400 response | Show allowed characters |
| **Engine load failure** | Model missing, GPU OOM | Exception on init | Fallback to CPU, show error |
| **GPU OOM** | Model too large | CUDA OOM error | Fallback to smaller model / CPU |
| **Timeout mid-synthesis** | Long text, slow engine | 504 timeout | Increase timeout or chunk |
| **Network disconnect** | Streaming client disconnects | Connection closed | Clean up resources |
| **Cancellation** | Client cancels | Client sends cancel | Stop synthesis, clean up |
| **Reconnection** | Client reconnects | New request with same ID | Resume (if engine supports) or restart |

## Tier classification

| Sub-item | Tier | Mery's priority |
|---|---|---|
| Health endpoint | Tier 1 BASE | P0 (ADR-0005 already has /v1/health) |
| Ready/live endpoints | Tier 2 COMMON | P1 |
| Metrics (Prometheus) | Tier 1 BASE (production) | P0 (before v1.0) |
| GPU management | Tier 1 BASE (production) | P0 (multi-engine support) |
| Model warmup | Tier 2 COMMON | P1 |
| Dynamic batching | Tier 3 PROVIDER-SPECIFIC | P2 (opt-in) |
| Concurrency limits | Tier 1 BASE (production) | P0 |
| Per-request timeout | Tier 1 BASE (production) | P0 |
| Client cancellation | Tier 1 BASE (UX) | P1 |
| Graceful shutdown | Tier 1 BASE (ops) | P1 |
| Streaming backpressure | Tier 2 COMMON (streaming) | P1 |
| Failure mode catalog | Tier 1 BASE (correctness) | **P0 (test coverage)** |

## Reference projects

- [ElevenLabs API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert) — error schema
- [OpenAI error codes](https://platform.openai.com/docs/guides/error-codes) — standardized errors
- [RealtimeTTS](https://koljab.github.io/RealtimeTTS/en/usage/) — streaming callbacks
- [LiveKit Agents TTS](https://github.com/livekit/agents) — `TTSCapabilities`, `StreamAdapter`
- [Azure Speech SDK](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/) — error handling patterns
- [Prometheus Python client](https://github.com/prometheus/client_python) — metrics
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/) — tracing

## Decisions needed (future ADR)

1. **Metrics format:** Prometheus (pull) vs OpenTelemetry (push)?
2. **Tracing:** OpenTelemetry for distributed tracing across client→server?
3. **Batching policy:** opt-in (per-request) vs always-on (server decides)?
4. **Multi-GPU:** Phase 1 single GPU, or Phase 2 multi-GPU from start?
5. **Failure mode tests:** which 9 modes have explicit contract tests?

## Cross-references

- `axes/01-engine-layer.md` — engine capabilities for cancellation
- `axes/02-protocol.md` — TTFB SLA definition
- `99-priority-matrix.md` — sequencing
