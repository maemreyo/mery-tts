# Core Runtime Contract

**Status:** Active contract for console and client work  
**Source:** ADR-0037 — Core Runtime Contract Before Console Expansion

This document defines the backend guarantees that every client consumes through `/v1`. The Console, CLI helpers, browser extensions, desktop apps, and agents must treat the runtime as the source of truth and must not infer or duplicate backend behavior in UI code.

## Ownership boundary

Mery owns local runtime behavior: engines, installed voices, catalog/install state, readiness, synthesis, fallback, streaming, diagnostics, errors, and server-owned storage. Clients own presentation and user interaction only.

The Console consumes runtime behavior through `/v1` and generated client types only. Console code must not duplicate install state machines, voice resolution, provider fallback, streaming semantics, diagnostic sanitization, storage layout, or readiness rules.

Model training, voice quality competition, and model fine-tuning are out of scope. Mery integrates engines/providers and makes their local runtime behavior reliable.

## Engine contract

Engines expose stable adapter capabilities, health, synthesis, optional annotated synthesis, cancellation, and streaming capability metadata. Engine discovery and health must remain deterministic without importing unavailable optional packages during normal checks.

Required evidence:

- fake-engine adapter tests for health and synthesis behavior
- API contract tests for `/v1/engines`
- optional real-engine smoke tests marked separately when dependencies exist

## Voice contract

Installed voices resolve through backend registries/resolvers. Voice payloads and metadata are serialized through `/v1` schemas. Active synthesis sessions retain adapter references safely across registry refreshes.

Required evidence:

- installed voice schema tests
- unknown voice failure tests through public APIs
- refresh behavior tests without real model downloads

## Install/readiness contract

Install jobs expose durable, pollable, terminal state. The Console can render queued/running/succeeded/failed/cancelled states without understanding backend internals.

Readiness responses expose ready/not-ready decisions, usable voice counts, provider/runtime summaries, smoke status, and actionable next steps from backend-owned data.

Required evidence:

- API contract tests for install start/poll terminal states
- health/readiness tests for live, ready, degraded, unavailable, and not-ready states
- fake install worker tests without network access

## Synthesis contract

All transports use shared synthesis orchestration for voice planning, fallback, diagnostics, locale checks, runtime policy, and audio metadata. Blocking OpenAI-compatible speech and future Console playback must not implement separate fallback logic.

Required evidence:

- fake-engine tests for success, unsupported model, unsupported format, missing voice, fallback diagnostics, locale mismatch, and sanitized errors
- transport-neutral service tests for fallback plans and runtime resource policy
- API contract tests for `/v1/audio/speech`

## Streaming contract

Streaming is correctness-first. The runtime owns first-chunk metadata, raw PCM semantics, cancellation, sequence assignment, adaptive backpressure, post-first-byte failure behavior, and capability reporting.

Required evidence:

- fake streaming tests for first-chunk metadata, cancellation, sequence assignment, metadata drift, and capability reporting
- API contract tests for `stream=true + response_format=pcm`
- optional real uvicorn/real-engine smoke tests when runtime dependencies are available

## Error/diagnostic contract

Structured errors use stable machine-readable codes, recommended actions, fallback policies, help topics, and sanitized diagnostics. Diagnostics, history, exports, and audit logs must not include raw input text, tokens, API keys, reference audio, private URLs, or private filesystem paths.

Required evidence:

- sanitizer tests for structured errors and diagnostics export
- API contract tests for user-mode recovery and developer-mode diagnostic payloads
- local help topic mapping tests for user-actionable errors

## Storage contract

Runtime state uses server-owned platform paths. Storage identities use model IDs, voice IDs, artifact IDs, and catalog IDs instead of raw user paths.

Diagnostics history, playground history, settings, and local-only measurements may be backed by current file stores first and future SQLite later behind repository interfaces. Runtime synthesis correctness, voice resolution, install correctness, and readiness correctness must not depend on database availability.

Corrupt or unavailable diagnostics-history storage must degrade safely and emit sanitized diagnostics.

Required evidence:

- file-store boundary tests
- corruption recovery tests
- tests proving synthesis/install paths do not require diagnostics-history storage

## Test contract

Fake-engine deterministic tests are the default gate for normal development and CI. They must not require real engine packages, model downloads, accelerator hardware, or network access.

Optional real-engine smoke tests are marked separately and run only when dependencies and local models are available. Real smoke validates packaging/runtime integration; fake tests remain the correctness contract.

## Console dependency rule

Before adding or changing Console behavior, verify the backing `/v1` runtime contract and fake-engine tests first. If the Console needs behavior not exposed by `/v1`, add or harden the backend contract before adding UI state.
