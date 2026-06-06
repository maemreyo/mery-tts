"""PCM stream metadata extraction and stability validation.

ADR-0032: the first chunk establishes the stream contract (sample rate,
channels, sample width, encoding). Subsequent chunks are validated against
that contract. Drift terminates the stream with a structured lifecycle
error.
"""

from __future__ import annotations

from dataclasses import dataclass

from mery_tts.engines.base import HTTP_PCM_ENCODING, PCMChunk, PCMEncoding


class StreamMetadataError(ValueError):
    """Raised when a chunk's metadata drifts from the stream's contract.

    Subclasses ``ValueError`` so legacy callers that catch ``ValueError``
    still observe the failure mode, while typed handlers can match on this
    specific exception.
    """


@dataclass(frozen=True, slots=True)
class PCMStreamMetadata:
    """Stream contract derived from the first chunk."""

    sample_rate_hz: int
    channels: int
    sample_width_bytes: int
    encoding: PCMEncoding

    def is_compatible(self, chunk: PCMChunk) -> bool:
        return (
            chunk.sample_rate_hz == self.sample_rate_hz
            and chunk.channels == self.channels
            and chunk.sample_width_bytes == self.sample_width_bytes
            and chunk.encoding == self.encoding
        )

    def validate(self, chunk: PCMChunk) -> None:
        if not self.is_compatible(chunk):
            raise StreamMetadataError(
                "unstable PCM metadata: "
                f"chunk=(sr={chunk.sample_rate_hz}, ch={chunk.channels}, "
                f"sw={chunk.sample_width_bytes}, enc={chunk.encoding}); "
                f"contract=(sr={self.sample_rate_hz}, ch={self.channels}, "
                f"sw={self.sample_width_bytes}, enc={self.encoding})"
            )


def derive_stream_metadata(chunk: PCMChunk) -> PCMStreamMetadata:
    """Derive a stream contract from the first chunk."""
    if chunk.sample_rate_hz <= 0:
        raise StreamMetadataError(f"invalid sample_rate_hz: {chunk.sample_rate_hz}")
    if chunk.channels <= 0:
        raise StreamMetadataError(f"invalid channels: {chunk.channels}")
    if chunk.sample_width_bytes <= 0:
        raise StreamMetadataError(f"invalid sample_width_bytes: {chunk.sample_width_bytes}")
    return PCMStreamMetadata(
        sample_rate_hz=chunk.sample_rate_hz,
        channels=chunk.channels,
        sample_width_bytes=chunk.sample_width_bytes,
        encoding=chunk.encoding,
    )


def assert_http_encoding(chunk: PCMChunk) -> None:
    """Reject chunks whose encoding is not supported by P1 HTTP streaming."""
    if chunk.encoding != HTTP_PCM_ENCODING:
        raise StreamMetadataError(
            f"HTTP streaming only supports {HTTP_PCM_ENCODING}; got '{chunk.encoding}'"
        )
