"""Tests for the streaming package configuration and metadata primitives."""

from __future__ import annotations

import pytest

from mery_tts.engines.base import HTTP_PCM_ENCODING, PCMChunk
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.metadata import (
    PCMStreamMetadata,
    StreamMetadataError,
    assert_http_encoding,
    derive_stream_metadata,
)


def test_streaming_config_defaults_are_safe() -> None:
    config = StreamingConfig()
    assert config.backpressure_enabled is True
    assert config.backpressure_max_queue_size == 16
    assert config.backpressure_put_timeout_seconds == 5.0
    assert config.first_chunk_timeout_seconds == 30.0


def test_derive_stream_metadata_accepts_first_chunk() -> None:
    chunk = PCMChunk(
        pcm=b"abc",
        sample_rate_hz=24_000,
        channels=1,
        sample_width_bytes=2,
        encoding="pcm_s16le",
    )
    metadata = derive_stream_metadata(chunk)
    assert metadata == PCMStreamMetadata(
        sample_rate_hz=24_000,
        channels=1,
        sample_width_bytes=2,
        encoding="pcm_s16le",
    )


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("sample_rate_hz", 0),
        ("channels", 0),
        ("sample_width_bytes", 0),
    ],
)
def test_derive_stream_metadata_rejects_invalid_first_chunk(
    field_name: str, bad_value: int
) -> None:
    base = {
        "pcm": b"x",
        "sample_rate_hz": 24_000,
        "channels": 1,
        "sample_width_bytes": 2,
        "encoding": "pcm_s16le",
    }
    base[field_name] = bad_value  # type: ignore[assignment]
    chunk = PCMChunk(**base)  # type: ignore[arg-type]
    with pytest.raises(StreamMetadataError):
        derive_stream_metadata(chunk)


def test_stream_metadata_validates_compatible_chunk() -> None:
    contract = PCMStreamMetadata(
        sample_rate_hz=24_000, channels=1, sample_width_bytes=2, encoding="pcm_s16le"
    )
    chunk = PCMChunk(
        pcm=b"x",
        sample_rate_hz=24_000,
        channels=1,
        sample_width_bytes=2,
        encoding="pcm_s16le",
    )
    assert contract.is_compatible(chunk)
    contract.validate(chunk)  # does not raise


@pytest.mark.parametrize(
    "field_name,bad_value",
    [
        ("sample_rate_hz", 48_000),
        ("channels", 2),
        ("sample_width_bytes", 4),
        ("encoding", "pcm_f32le"),
    ],
)
def test_stream_metadata_rejects_drift(field_name: str, bad_value: object) -> None:
    contract = PCMStreamMetadata(
        sample_rate_hz=24_000, channels=1, sample_width_bytes=2, encoding="pcm_s16le"
    )
    base = {
        "pcm": b"x",
        "sample_rate_hz": 24_000,
        "channels": 1,
        "sample_width_bytes": 2,
        "encoding": "pcm_s16le",
    }
    base[field_name] = bad_value  # type: ignore[assignment]
    chunk = PCMChunk(**base)  # type: ignore[arg-type]
    assert not contract.is_compatible(chunk)
    with pytest.raises(StreamMetadataError):
        contract.validate(chunk)


def test_assert_http_encoding_accepts_s16le() -> None:
    chunk = PCMChunk(
        pcm=b"x",
        sample_rate_hz=24_000,
        channels=1,
        sample_width_bytes=2,
        encoding="pcm_s16le",
    )
    assert_http_encoding(chunk)  # does not raise


def test_assert_http_encoding_rejects_f32le() -> None:
    chunk = PCMChunk(
        pcm=b"x",
        sample_rate_hz=24_000,
        channels=1,
        sample_width_bytes=2,
        encoding="pcm_f32le",
    )
    with pytest.raises(StreamMetadataError, match="HTTP streaming only supports"):
        assert_http_encoding(chunk)


def test_pcm_chunk_default_encoding_is_p1_http_format() -> None:
    chunk = PCMChunk(pcm=b"x", sample_rate_hz=24_000, channels=1)
    assert chunk.encoding == HTTP_PCM_ENCODING
    assert chunk.encoding == "pcm_s16le"
    assert chunk.sample_width_bytes == 2
    assert chunk.sequence == 0
