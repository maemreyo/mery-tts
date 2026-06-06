from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from mery_tts.audio.encoder import encode_wav
from mery_tts.engines.base import PCMChunk
from mery_tts.errors import ErrorCategory, ErrorCode, LocalTTSError, diagnostic_error


@dataclass(frozen=True, slots=True)
class ExportResult:
    path: Path
    duration_seconds: float
    file_size_bytes: int


class AudioExporter:
    async def export(self, stream: AsyncIterator[PCMChunk], path: Path) -> ExportResult:
        if path.suffix.lower() != ".wav":
            raise self._unsupported_format(path)

        chunks = [chunk async for chunk in stream]
        wav_bytes = encode_wav(chunks)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(wav_bytes)
        except OSError as exc:
            raise self._write_failed(path, exc) from exc

        first = chunks[0]
        total_samples = sum(len(chunk.pcm) for chunk in chunks) / 2 / first.channels
        return ExportResult(
            path=path,
            duration_seconds=total_samples / first.sample_rate_hz,
            file_size_bytes=path.stat().st_size,
        )

    def _unsupported_format(self, path: Path) -> LocalTTSError:
        suffix = path.suffix.lower() or "<none>"
        return diagnostic_error(
            code=ErrorCode.SYNTHESIS_UNSUPPORTED_FORMAT,
            category=ErrorCategory.SYNTHESIS,
            request_id="local",
            diagnostic={"export_format": suffix},
        )

    def _write_failed(self, path: Path, exc: OSError) -> LocalTTSError:
        return diagnostic_error(
            code=ErrorCode.STORAGE_WRITE_FAILED,
            category=ErrorCategory.STORAGE,
            request_id="local",
            diagnostic={"export_path": path.name, "reason": str(exc)},
        )
