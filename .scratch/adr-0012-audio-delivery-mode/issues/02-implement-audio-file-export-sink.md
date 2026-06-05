# Implement audio file export sink

Status: future

## Parent

ADR-0012 — `docs/adr/ADR-0012-audio-delivery-mode.md`

## What to build

Add `--output <file>` support to `mery speak` for batch audio export to disk.
This is the third audio delivery mode identified in ADR-0012 — a file-export
sink that requires no changes to the engine layer.

**`audio/exporter.py`**

Implement `AudioExporter` with an async `export(stream: AsyncIterator[PCMChunk], path: Path)` method that:
1. Infers output format from the file extension (`.wav`, `.mp3`, `.ogg`).
2. For `.wav`: writes a standard PCM WAV header then drains the chunk
   stream into the file.
3. For other formats: pipes PCM frames through `ffmpeg` (subprocess) to
   encode to the target format.
4. Returns an `ExportResult` with path, duration, file size.

**CLI integration**

Extend `mery speak` with:
```
--output <path>   Write synthesized audio to file instead of playing
--format <fmt>    Force output format (wav, mp3, ogg). Default: inferred from extension.
```

When `--output` is given, `--play` is ignored and the file export sink is used.

## Acceptance criteria

- [ ] `mery speak --text "Hello" --output hello.wav` produces a valid WAV file.
- [ ] `mery speak --file input.txt --output output.mp3` works end-to-end.
- [ ] `ExportResult` includes duration (seconds) and file size (bytes).
- [ ] Export errors (disk full, permission denied) map to the structured error
      taxonomy from ADR-0010.
- [ ] Unit tests cover: WAV export round-trip, unsupported format error,
      disk-full simulation.
- [ ] `audio/exporter.py` import graph: CLI-only, not importable from `api/`.

## Blocked by

- ADR-0012 issue 01 (player/encoder split must be done first)
- ADR-0004 issue 01 (PCMChunk schema)

## Comments

This issue is marked **future** because batch export is not required for the
first integration milestone. It should be prioritised once the core
synthesize → WebSocket path is working.
