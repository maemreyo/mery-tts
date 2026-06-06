"""Standalone modular streaming subsystem.

ADR-0031: P1 streaming lives here, not in route helpers. The package owns
transport-independent streaming mechanics: metadata validation, sequence
assignment, cancellation, adaptive backpressure, and HTTP adaptation. Fake
streaming utilities live under ``tests/fakes/streaming.py``.
"""

from mery_tts.streaming.backpressure import (
    BackpressureConfig,
    BackpressureTimeout,
    BoundedPCMQueue,
)
from mery_tts.streaming.cancellation import StreamCancellation
from mery_tts.streaming.capabilities import (
    StreamingCapability,
    StreamingCapabilityInfo,
    StreamingGranularity,
)
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.metadata import (
    PCMStreamMetadata,
    StreamMetadataError,
    derive_stream_metadata,
)
from mery_tts.streaming.pipeline import StreamingPipeline

__all__ = [
    "BackpressureConfig",
    "BackpressureTimeout",
    "BoundedPCMQueue",
    "PCMStreamMetadata",
    "StreamCancellation",
    "StreamMetadataError",
    "StreamingCapability",
    "StreamingCapabilityInfo",
    "StreamingConfig",
    "StreamingGranularity",
    "StreamingPipeline",
    "derive_stream_metadata",
]
