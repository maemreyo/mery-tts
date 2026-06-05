# ADR-0012 — Hybrid audio delivery mode

Status: accepted

## ADR

`docs/adr/ADR-0012-audio-delivery-mode.md`

## Source

Design Decision 10

## Summary

Hybrid delivery: CLI mode plays audio directly via `sounddevice`; WebSocket
client mode streams PCM16 chunks over `/v1/events`. Both modes consume the
same `AsyncIterator[PCMChunk]` from `EngineAdapter.synthesize()`. The
infrastructure split (player vs encoder) happens at Layer 3, not in the
domain. A future `--output <file>` export sink is a natural third mode with
no engine-layer changes required.

## Issues

- [`01-split-cli-playback-and-streaming-audio-sinks.md`](issues/01-split-cli-playback-and-streaming-audio-sinks.md) — ready-for-agent
- [`02-implement-audio-file-export-sink.md`](issues/02-implement-audio-file-export-sink.md) — future
