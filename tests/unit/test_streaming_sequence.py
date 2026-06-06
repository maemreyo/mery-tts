"""Tests for the transport sequence assignment and validation."""

from __future__ import annotations

import pytest

from mery_tts.engines.base import PCMChunk
from mery_tts.streaming.sequence import SequenceAssigner, StreamSequenceError


def _chunk(seq: int) -> PCMChunk:
    return PCMChunk(
        pcm=b"x",
        sample_rate_hz=24_000,
        channels=1,
        sequence=seq,
    )


def test_assigner_assigns_deterministic_sequence_to_zero_chunks() -> None:
    assigner = SequenceAssigner()
    out = [assigner.process(_chunk(0)) for _ in range(3)]
    assert [c.sequence for c in out] == [0, 1, 2]


def test_assigner_validates_explicit_monotonic_sequence() -> None:
    assigner = SequenceAssigner()
    out = [assigner.process(_chunk(i)) for i in range(3)]
    assert [c.sequence for c in out] == [0, 1, 2]


def test_assigner_detects_explicit_sequence_gap() -> None:
    assigner = SequenceAssigner()
    assigner.process(_chunk(0))
    with pytest.raises(StreamSequenceError, match="explicit sequence gap"):
        assigner.process(_chunk(2))


def test_assigner_does_not_mutate_input_chunk() -> None:
    chunk = _chunk(0)
    assigner = SequenceAssigner()
    out = assigner.process(chunk)
    assert chunk.sequence == 0
    assert out.sequence == 0
    assert out is not chunk


def test_assigner_substitutes_zero_chunk_with_counter_after_explicit_run() -> None:
    assigner = SequenceAssigner()
    assigner.process(_chunk(0))
    assigner.process(_chunk(1))
    out = assigner.process(_chunk(0))
    assert out.sequence == 2
