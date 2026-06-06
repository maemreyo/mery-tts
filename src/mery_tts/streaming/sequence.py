"""Transport sequence assignment and validation.

ADR-0032: pipeline assigns deterministic transport sequence numbers
(0, 1, 2, ...) for adapters that emit default ``sequence=0``. Adapters may
emit explicit non-zero sequences; the pipeline validates strict monotonic
increase.
"""

from __future__ import annotations

from dataclasses import dataclass

from mery_tts.engines.base import PCMChunk


class StreamSequenceError(ValueError):
    """Raised when a chunk's sequence violates the monotonic contract."""


@dataclass(slots=True)
class SequenceAssigner:
    """Assigns or validates transport sequence numbers for chunks.

    If the adapter emits non-zero explicit sequences, the assigner
    validates strict monotonic increase. If the adapter emits the default
    zero sequence, the assigner substitutes its own deterministic counter.
    """

    _next: int = 0

    def process(self, chunk: PCMChunk) -> PCMChunk:
        if chunk.sequence == 0:
            index = self._next
            self._next += 1
            return _replace_sequence(chunk, index)
        if chunk.sequence != self._next:
            raise StreamSequenceError(
                f"explicit sequence gap: adapter emitted {chunk.sequence}, expected {self._next}"
            )
        self._next += 1
        return chunk


def _replace_sequence(chunk: PCMChunk, sequence: int) -> PCMChunk:
    # PCMChunk is frozen=True. Construct a new instance with the
    # transport-assigned sequence while preserving every other field.
    return PCMChunk(
        pcm=chunk.pcm,
        sample_rate_hz=chunk.sample_rate_hz,
        channels=chunk.channels,
        sample_width_bytes=chunk.sample_width_bytes,
        encoding=chunk.encoding,
        sequence=sequence,
    )
