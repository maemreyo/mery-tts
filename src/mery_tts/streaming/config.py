"""Typed server-side streaming configuration.

ADR-0031: injected by the app factory; not exposed as client request knobs.
ADR-0033: bounded queue parameters for decoupled producers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StreamingConfig:
    """Server-side configuration for the streaming subsystem.

    Native async streams skip the bounded queue entirely; decoupled or
    thread-backed producers use ``backpressure`` to bound memory.
    """

    backpressure_enabled: bool = True
    backpressure_max_queue_size: int = 16
    backpressure_put_timeout_seconds: float = 5.0
    # First-chunk fetch timeout for header derivation. Should be short —
    # the client is waiting for response headers to arrive.
    first_chunk_timeout_seconds: float = 30.0
