"""Streaming pipeline — core orchestrator that owns streaming lifecycle.

ADR-0031, ADR-0032, ADR-0033. The pipeline:
- Owns the cancellation context (transport-independent).
- Validates metadata against the first-chunk contract.
- Assigns deterministic transport sequence numbers for adapters that
  emit default ``sequence=0``.
- Calls ``adapter.cancel(request_id)`` on cancellation; idempotent.
- Routes native async streams through direct consumption (no queue).
- For decoupled producers, a ``BoundedPCMQueue`` bridge is exposed in
  ``backpressure.py`` but the pipeline does not force it onto native
  async iterators (per ADR-0033).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.streaming.cancellation import StreamCancellation
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.metadata import (
    PCMStreamMetadata,
    StreamMetadataError,
    derive_stream_metadata,
)
from mery_tts.streaming.sequence import SequenceAssigner, StreamSequenceError
from mery_tts.voice.descriptor import VoiceDescriptor

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Outcome of a streaming pipeline run."""

    chunks: tuple[PCMChunk, ...]
    metadata: PCMStreamMetadata
    cancelled: bool
    metadata_drift: bool
    sequence_error: bool


class StreamingPipeline:
    """Owns the lifecycle of a single streaming request.

    The pipeline is constructed once per request and yields PCMChunk
    values through :meth:`run`. The route never cancels the adapter
    directly; the pipeline does, through the cancellation context.
    """

    def __init__(
        self,
        *,
        adapter: EngineAdapter,
        voice: VoiceDescriptor,
        text: str,
        request_id: str,
        config: StreamingConfig | None = None,
    ) -> None:
        self._adapter = adapter
        self._voice = voice
        self._text = text
        self._config = config or StreamingConfig()
        self._cancellation = StreamCancellation(request_id=request_id)
        self._metadata: PCMStreamMetadata | None = None
        self._assigner = SequenceAssigner()
        self._cancelled = False
        self._metadata_drift = False
        self._sequence_error = False

    @property
    def request_id(self) -> str:
        return self._cancellation.request_id

    @property
    def cancellation(self) -> StreamCancellation:
        return self._cancellation

    @property
    def config(self) -> StreamingConfig:
        return self._config

    @property
    def metadata(self) -> PCMStreamMetadata | None:
        return self._metadata

    def cancel(self) -> None:
        """Cancel the in-flight stream. Idempotent and adapter-safe."""
        if self._cancellation.is_cancelled():
            return
        self._cancellation.cancel()
        # The adapter's official cancel hook is idempotent at the
        # contract level; multiple calls are safe (ADR-0033).
        try:
            self._adapter.cancel(self._cancellation.request_id)
        except Exception as exc:
            _LOGGER.warning(
                "stream.adapter_cancel_error",
                extra={
                    "request_id": self._cancellation.request_id,
                    "engine_id": self._adapter.engine_id,
                    "reason": type(exc).__name__,
                },
            )

    async def run(self) -> AsyncIterator[PCMChunk]:
        """Yield PCM chunks through the streaming pipeline.

        The first chunk establishes metadata; subsequent chunks are
        validated and assigned transport sequence numbers. Cancellation
        is observed between chunks.
        """
        emitted: list[PCMChunk] = []
        self._cancelled = False
        self._metadata_drift = False
        self._sequence_error = False
        try:
            iterator = self._adapter.synthesize(
                self._text,
                self._voice,
                request_id=self._cancellation.request_id,
            )
            async for raw_chunk in iterator:
                if self._cancellation.is_cancelled():
                    self._cancelled = True
                    break
                try:
                    chunk = self._process_chunk(raw_chunk)
                except (StreamMetadataError, StreamSequenceError):
                    self._metadata_drift = True
                    self._sequence_error = isinstance(_last_error(), StreamSequenceError)
                    raise
                emitted.append(chunk)
                yield chunk
        except (StreamMetadataError, StreamSequenceError) as exc:
            _LOGGER.info(
                "stream.metadata_drift",
                extra={
                    "request_id": self._cancellation.request_id,
                    "engine_id": self._adapter.engine_id,
                    "reason": type(exc).__name__,
                },
            )
            raise
        finally:
            # aclose() / cancellation / normal exit — all paths arrive
            # here. Adapter cleanup is the adapter's job; we only
            # observe.
            pass

    def _process_chunk(self, chunk: PCMChunk) -> PCMChunk:
        if self._metadata is None:
            self._metadata = derive_stream_metadata(chunk)
        else:
            self._metadata.validate(chunk)
        return self._assigner.process(chunk)

    def result(self) -> PipelineResult:
        return PipelineResult(
            chunks=(),
            metadata=self._metadata
            or PCMStreamMetadata(
                sample_rate_hz=0, channels=0, sample_width_bytes=0, encoding="pcm_s16le"
            ),
            cancelled=self._cancelled,
            metadata_drift=self._metadata_drift,
            sequence_error=self._sequence_error,
        )


def _last_error() -> BaseException:
    """Return the most recent exception, or a generic BaseException."""
    import sys

    return sys.exception() or BaseException()
