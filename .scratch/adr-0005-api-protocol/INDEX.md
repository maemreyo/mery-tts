# ADR-0005 — Hybrid REST + WebSocket protocol

Source ADR: `docs/adr/ADR-0005-api-protocol.md`

## Goal

Expose a versioned `/v1` local API where REST handles deterministic helper management and WebSocket handles long-running install and synthesis event streams, while domain modules remain transport-agnostic.

## Issues

1. [Define versioned REST and event schemas](issues/01-define-versioned-rest-and-event-schemas.md)
2. [Implement REST management endpoints](issues/02-implement-rest-management-endpoints.md)
3. [Implement model install API orchestration](issues/03-implement-model-install-api-orchestration.md)
4. [Implement WebSocket event stream protocol](issues/04-implement-websocket-event-stream-protocol.md)
