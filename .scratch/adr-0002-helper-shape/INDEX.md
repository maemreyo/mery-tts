# ADR-0002 — Helper shape: CLI + daemon hybrid

Source ADR: `docs/adr/ADR-0002-helper-shape.md`

## Goal

Build one Python helper package that exposes both `mery` CLI workflows and long-running daemon/server mode, while sharing engine, model, catalog, and diagnostics logic.

## Issues

1. [Create CLI entrypoint and command skeleton](issues/01-create-cli-entrypoint-and-command-skeleton.md)
2. [Create daemon app factory and serve command](issues/02-create-daemon-app-factory-and-serve-command.md)
3. [Split CLI playback and streaming audio sinks](issues/03-split-cli-playback-and-streaming-audio-sinks.md)
