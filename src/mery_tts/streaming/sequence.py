"""Transport sequence assignment and validation.

ADR-0032: the pipeline assigns deterministic transport sequence numbers
(0, 1, 2, ...) for adapters that emit the default ``sequence=0`` on
every chunk, OR validates strict monotonic increase starting from 0 for
adapters that emit explicit non-zero sequences. The mode is locked by
the first chunk — adapters MUST NOT mix the two modes in one stream.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from mery_tts.engines.base import PCMChunk


class StreamSequenceError(ValueError):
    """Raised when a chunk's sequence violates the monotonic contract."""


class SequenceMode(Enum):
    """Per-stream sequence mode, locked by the first chunk."""

    IMPLICIT = "implicit"
    EXPLICIT = "explicit"


@dataclass(slots=True)
class SequenceAssigner:
    """Assigns or validates transport sequence numbers for chunks.

    The mode is fixed by the first chunk:
    - ``sequence == 0`` → IMPLICIT mode: the assigner substitutes its
      own deterministic counter (0, 1, 2, ...).
    - ``sequence != 0`` → EXPLICIT mode: the assigner validates strict
      monotonic increase starting from the first chunk's value.

    Mixing modes within a single stream raises ``StreamSequenceError``.
    """

    _next: int = 0
    _mode: SequenceMode | None = None

    def process(self, chunk: PCMChunk) -> PCMChunk:
        if self._mode is None:
            if chunk.sequence == 0:
                self._mode = SequenceMode.IMPLICIT
            else:
                self._mode = SequenceMode.EXPLICIT
                self._next = chunk.sequence
        if self._mode is SequenceMode.IMPLICIT:
            if chunk.sequence != 0:
                raise StreamSequenceError(
                    "stream locked to implicit mode; chunk emitted explicit "
                    f"sequence={chunk.sequence}"
                )
            index = self._next
            self._next += 1
            return _replace_sequence(chunk, index)
        if chunk.sequence == 0:
            raise StreamSequenceError(
                "stream locked to explicit mode; chunk emitted implicit sequence=0"
            )
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
