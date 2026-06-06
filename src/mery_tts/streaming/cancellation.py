"""Transport-independent streaming cancellation.

ADR-0033: pipeline owns the cancellation context. The route does not call
adapter cancellation directly. The cancellation context is a single
asyncio.Event that is safe within the async pipeline; thread-backed
bridges must use a thread-safe signal — see ``backpressure`` for that
side of the contract.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass(slots=True)
class StreamCancellation:
    """Cancellation context for one streaming request.

    The ``cancelled`` event is set exactly once, regardless of how many
    times ``cancel()`` is called. ``is_cancelled()`` is non-blocking and
    safe to call from any async task within the same event loop.
    """

    request_id: str
    cancelled: asyncio.Event = field(default_factory=asyncio.Event)

    def cancel(self) -> None:
        self.cancelled.set()

    def is_cancelled(self) -> bool:
        return self.cancelled.is_set()
