"""Streaming capability models exposed to discovery endpoints.

ADR-0035: the capability taxonomy is the truth about what a provider
can do. Capability is layered: adapter static baseline + installed
voice/model metadata + runtime health. The capability model is
serialized to snake_case enum strings on the wire.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class StreamingCapability(StrEnum):
    """How a provider can stream raw PCM."""

    NOT_SUPPORTED = "not_supported"
    ROUTE_CHUNKED = "route_chunked"
    SENTENCE_CHUNKED = "sentence_chunked"
    NATIVE_INCREMENTAL = "native_incremental"


StreamingGranularity = Literal["none", "sentence", "chunk", "token"]


@dataclass(frozen=True, slots=True)
class StreamingCapabilityInfo:
    """Capability payload for a single engine or installed voice."""

    supported: bool
    mode: StreamingCapability
    granularity: StreamingGranularity = "none"
    true_incremental: bool = False
    format: str = "pcm_s16le"
    sample_rates_hz: tuple[int, ...] = ()
