# Complete HTTP local-usable contract

Status: completed

## Parent

ADR-0021 — `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`

## What to build

Complete the HTTP-first local usable contract so Zam Reader can pair, authenticate, inspect readiness, and call `/v1/audio/speech` without WebSocket streaming. This slice defines the minimum runtime surface for local experimental/degraded use.

## Acceptance criteria

- [x] `/v1/health` includes helper identity, helper version, contract version, readiness status, engine summaries, and usable voice counts.
- [x] HTTP CORS/preflight handling allows configured localhost/extension usage without wildcard credentials.
- [x] `Access-Control-Expose-Headers` includes the `X-Mery-*` diagnostics headers used by audio responses.
- [x] `/v1/audio/speech` remains the first local usable transport and does not require `/v1/events`.

## Production-ready criteria

- [x] Contract tests cover health shape, compatible/incompatible contract versions, CORS preflight, and exposed diagnostics headers.
- [x] Invalid auth/origin requests still fail with structured errors and no sensitive diagnostics.
- [x] Docs state that WebSocket streaming is deferred from the first local usable milestone.

## Blocked by

- None - can start immediately
