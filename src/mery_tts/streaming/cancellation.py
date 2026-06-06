"""Transport-independent streaming cancellation.

ADR-0033: pipeline owns the cancellation context. The route does not call
adapter cancellation directly. The cancellation context is a single
asyncio.Event that is safe within the async pipeline; thread-backed
bridges must use a thread-safe signal — see ``backpressure`` for that
side of the contract.

WARNING: ``StreamCancellation.cancel()`` calls ``asyncio.Event.set()`` and
is only safe to call from within the event loop that owns the event.
Callers running in a worker thread MUST dispatch via
``loop.call_soon_threadsafe(self.cancel)`` to avoid undefined behavior.
``pipeline.cancel()`` does NOT auto-dispatch — it calls
``self._cancellation.cancel()`` directly, so it inherits the same
restriction. The intended entry point for in-loop code is
``pipeline.cancel()``; the intended entry point for worker threads is
``asyncio.get_event_loop().call_soon_threadsafe(pipeline.cancel)``.
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

    WARNING: ``cancel()`` must not be called from a worker thread. Use
    ``loop.call_soon_threadsafe(self.cancel)`` to dispatch the call
    onto the event loop. ``pipeline.cancel()`` has the same restriction
    and is safe only from in-loop code.
    """

    request_id: str
    cancelled: asyncio.Event = field(default_factory=asyncio.Event)

    def cancel(self) -> None:
        self.cancelled.set()

    def is_cancelled(self) -> bool:
        return self.cancelled.is_set()
