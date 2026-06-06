"""Tests for the adaptive backpressure primitives."""

from __future__ import annotations

import asyncio
import threading

import pytest

from mery_tts.engines.base import PCMChunk
from mery_tts.streaming.backpressure import (
    BackpressureConfig,
    BackpressureTimeout,
    BoundedPCMQueue,
)


def _chunk(payload: bytes) -> PCMChunk:
    return PCMChunk(pcm=payload, sample_rate_hz=24_000, channels=1)


@pytest.mark.asyncio
async def test_bounded_queue_preserves_chunks_under_consumer_pressure() -> None:
    config = BackpressureConfig(max_queue_size=2, put_timeout_seconds=2.0)
    queue_ = BoundedPCMQueue(config=config)

    received: list[bytes] = []

    async def consumer() -> None:
        async for chunk in queue_.aiter_chunks():
            received.append(chunk.pcm)

    consumer_task = asyncio.create_task(consumer())
    # Producer that interleaves with consumer so the queue never stays
    # full — proves the queue does not drop chunks under normal pressure.
    for index in range(6):
        queue_.put(_chunk(f"chunk-{index}".encode()))
        await asyncio.sleep(0.01)
    queue_.close()
    await consumer_task

    assert received == [f"chunk-{index}".encode() for index in range(6)]


@pytest.mark.asyncio
async def test_bounded_queue_raises_backpressure_timeout_when_full() -> None:
    # Tiny queue, zero put timeout — second put will fail.
    config = BackpressureConfig(max_queue_size=1, put_timeout_seconds=0.01)
    queue_ = BoundedPCMQueue(config=config)

    queue_.put(_chunk(b"first"))
    with pytest.raises(BackpressureTimeout):
        queue_.put(_chunk(b"second"))


@pytest.mark.asyncio
async def test_bounded_queue_close_unblocks_consumer() -> None:
    config = BackpressureConfig(max_queue_size=2, put_timeout_seconds=0.1)
    queue_ = BoundedPCMQueue(config=config)

    received: list[bytes] = []

    async def consumer() -> None:
        async for chunk in queue_.aiter_chunks():
            received.append(chunk.pcm)

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.01)
    queue_.put(_chunk(b"a"))
    queue_.put(_chunk(b"b"))
    await asyncio.sleep(0.01)
    queue_.close()
    await task

    assert received == [b"a", b"b"]


@pytest.mark.asyncio
async def test_bounded_queue_put_after_close_raises_timeout() -> None:
    config = BackpressureConfig(max_queue_size=2, put_timeout_seconds=0.01)
    queue_ = BoundedPCMQueue(config=config)
    queue_.close()
    with pytest.raises(BackpressureTimeout):
        queue_.put(_chunk(b"late"))


def test_thread_backed_bridge_runs_producer_in_daemon_thread() -> None:
    """Verify the thread-backed bridge helper drives a sync producer safely."""
    from mery_tts.streaming.backpressure import bridge_thread_producer

    config = BackpressureConfig(max_queue_size=8, put_timeout_seconds=1.0)
    queue_ = BoundedPCMQueue(config=config)
    producer_started = threading.Event()
    producer_finished = threading.Event()

    def producer() -> None:
        producer_started.set()
        for index in range(3):
            queue_.put(_chunk(f"thread-{index}".encode()))
        producer_finished.set()

    thread = bridge_thread_producer(producer_callable=producer, queue_=queue_)
    thread.start()
    assert producer_started.wait(timeout=1.0)
    assert producer_finished.wait(timeout=1.0)
    thread.join(timeout=1.0)
    assert not thread.is_alive()
