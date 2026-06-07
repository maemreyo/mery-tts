"""Tests for the transport sequence assignment and validation."""

from __future__ import annotations

import pytest

from mery_tts.engines.base import PCMChunk
from mery_tts.streaming.sequence import (
    SequenceAssigner,
    SequenceMode,
    StreamSequenceError,
)


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


def test_assigner_validates_explicit_monotonic_sequence_starting_above_zero() -> None:
    assigner = SequenceAssigner()
    out = [assigner.process(_chunk(i)) for i in range(1, 4)]
    assert [c.sequence for c in out] == [1, 2, 3]


def test_assigner_detects_explicit_sequence_gap() -> None:
    assigner = SequenceAssigner()
    assigner.process(_chunk(1))
    with pytest.raises(StreamSequenceError, match="explicit sequence gap"):
        assigner.process(_chunk(3))


def test_assigner_does_not_mutate_input_chunk() -> None:
    chunk = _chunk(0)
    assigner = SequenceAssigner()
    out = assigner.process(chunk)
    assert chunk.sequence == 0
    assert out.sequence == 0
    assert out is not chunk


def test_assigner_locks_implicit_mode_on_first_zero_chunk() -> None:
    assigner = SequenceAssigner()
    assigner.process(_chunk(0))
    with pytest.raises(StreamSequenceError, match="stream locked to implicit mode"):
        assigner.process(_chunk(1))


def test_assigner_accepts_explicit_sequence_starting_above_zero() -> None:
    assigner = SequenceAssigner()
    first = assigner.process(_chunk(5))
    assert first.sequence == 5
    second = assigner.process(_chunk(6))
    assert second.sequence == 6


def test_assigner_rejects_implicit_chunk_after_explicit_run() -> None:
    assigner = SequenceAssigner()
    assigner.process(_chunk(1))
    assigner.process(_chunk(2))
    with pytest.raises(StreamSequenceError, match="stream locked to explicit mode"):
        assigner.process(_chunk(0))


def test_assigner_exposes_mode_after_first_chunk() -> None:
    assigner = SequenceAssigner()
    assert assigner._mode is None
    assigner.process(_chunk(0))
    assert assigner._mode is SequenceMode.IMPLICIT

    explicit_assigner = SequenceAssigner()
    explicit_assigner.process(_chunk(1))
    assert explicit_assigner._mode is SequenceMode.EXPLICIT
