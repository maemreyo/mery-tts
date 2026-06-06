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

- [x] `mery speak --text "Hello" --output hello.wav` produces a valid WAV file. Current implementation writes deterministic local PCM through the CLI-only WAV export sink without optional engine downloads.
- [ ] `mery speak --file input.txt --output output.mp3` works end-to-end.
  - Progress: `mery speak --file input.txt --output output.wav` now reads text from disk and exports through the CLI-only WAV sink end-to-end; MP3 encoder support remains pending.
- [x] `ExportResult` includes duration (seconds) and file size (bytes). `AudioExporter.export()` returns path, duration seconds, and file size bytes for WAV exports.
- [ ] Export errors (disk full, permission denied) map to the structured error
      taxonomy from ADR-0010.
  - Progress: `AudioExporter` routes unsupported formats and WAV write failures through the shared ADR-0010 `diagnostic_error()` factory. Unsupported formats map to central `synthesis.unsupported_format` no-action/no-fallback metadata; disk-full and permission-denied write failures map to `storage.write_failed` with `free_space` action and fail-closed diagnostics that omit embedded local paths. Non-WAV encoder paths remain pending.
- [x] Unit tests cover: WAV export round-trip, unsupported format error,
      disk-full simulation. `tests/unit/test_audio_sinks.py` covers valid WAV metadata/round-trip, unsupported format structured error mapping, and disk-full/write-failure simulation with sanitized diagnostics.
- [x] `audio/exporter.py` import graph: CLI-only, not importable from `api/`. Package-boundary tests scan `src/mery_tts/api/**` and fail if any API module imports `mery_tts.audio.exporter`.

## Blocked by

- ADR-0012 issue 01 (player/encoder split must be done first)
- ADR-0004 issue 01 (PCMChunk schema)

## Comments

This issue is marked **future** because batch export is not required for the
first integration milestone. It should be prioritised once the core
synthesize → WebSocket path is working.
