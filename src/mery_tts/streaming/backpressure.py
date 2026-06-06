"""Adaptive backpressure primitives for decoupled producers.

ADR-0033: native async streams skip the queue entirely. Decoupled or
thread-backed producers (e.g. adapters that bridge a worker thread into
the async loop) can use ``BoundedPCMQueue`` to bound memory while
preserving every chunk. Queue-full timeout cancels the stream and
surfaces a ``BackpressureTimeout`` lifecycle error.
"""

from __future__ import annotations

import asyncio
import contextlib
import queue
import threading
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from mery_tts.engines.base import PCMChunk


class BackpressureTimeout(Exception):
    """Raised when a producer cannot enqueue a chunk within the put timeout.

    Surfaces as a streaming lifecycle error: ``stream_backpressure_timeout``.
    Cancellation is the only safe response — dropping audio would corrupt
    playback, and the consumer must release the buffer.
    """


@dataclass(frozen=True, slots=True)
class BackpressureConfig:
    """Configuration for a bounded queue bridge."""

    max_queue_size: int = 16
    put_timeout_seconds: float = 5.0


class BoundedPCMQueue:
    """Thread-safe bounded queue bridging a worker thread into async.

    Producer (thread) calls ``put()``. Async consumer iterates with
    ``aiter_chunks()``. On queue full, ``put()`` blocks up to the
    configured timeout then raises ``BackpressureTimeout``. ``close()``
    terminates the consumer; the consumer side finishes naturally when
    the queue drains and ``close()`` is called.

    This primitive is intentionally NOT used by ``StreamingPipeline`` for
    native async streams; see ADR-0033 — the pipeline consumes
    ``AsyncIterator[PCMChunk]`` directly. The queue is exposed for
    decoupled producers (e.g. future thread-backed incremental adapters).
    """

    def __init__(self, *, config: BackpressureConfig | None = None) -> None:
        self._config = config or BackpressureConfig()
        self._queue: queue.Queue[PCMChunk | None] = queue.Queue(maxsize=self._config.max_queue_size)
        self._closed = False
        self._lock = threading.Lock()

    @property
    def config(self) -> BackpressureConfig:
        return self._config

    def put(self, chunk: PCMChunk) -> None:
        """Producer-side: enqueue one chunk, blocking up to the timeout."""
        if self._closed:
            raise BackpressureTimeout("queue is closed")
        try:
            self._queue.put(chunk, timeout=self._config.put_timeout_seconds)
        except queue.Full as exc:
            raise BackpressureTimeout(
                f"queue full after {self._config.put_timeout_seconds}s"
            ) from exc

    def close(self) -> None:
        """Producer-side: signal end-of-stream to the consumer."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        # Sentinel is also bounded — use a non-blocking put when full.
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            # Drain one item, then close.
            with contextlib.suppress(queue.Empty):
                self._queue.get_nowait()
            self._queue.put_nowait(None)

    async def aiter_chunks(self) -> AsyncIterator[PCMChunk]:
        """Async consumer: yield each chunk until the producer closes."""
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, self._queue.get)
            if chunk is None:
                return
            yield chunk


def bridge_thread_producer(
    *,
    producer_callable: Callable[[], None],
    queue_: BoundedPCMQueue,
) -> threading.Thread:
    """Spawn a daemon thread that drives a synchronous producer into a queue.

    This is a thread-safe coordination helper. The producer callable is
    responsible for calling ``queue_.put(chunk)`` for each PCMChunk and
    finally ``queue_.close()``. If the producer raises, the queue is
    closed so the consumer does not hang.

    Cancellation of the async pipeline must call ``adapter.cancel()``
    separately (ADR-0033) — the thread will not see asyncio events.
    """
    thread = threading.Thread(
        target=_run_thread_producer,
        args=(producer_callable, queue_),
        daemon=True,
        name="mery-streaming-producer",
    )
    return thread


def _run_thread_producer(producer_callable: Callable[[], None], queue_: BoundedPCMQueue) -> None:
    try:
        producer_callable()
    except Exception:
        # Surface as a stream lifecycle error to the consumer by closing
        # the queue; BackpressureTimeout elsewhere is the right path.
        queue_.close()
        raise
    finally:
        queue_.close()
