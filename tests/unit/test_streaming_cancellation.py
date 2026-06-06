"""Tests for the streaming cancellation context."""

from __future__ import annotations

import asyncio

import pytest

from mery_tts.streaming.cancellation import StreamCancellation


def test_cancellation_starts_not_cancelled() -> None:
    cancellation = StreamCancellation(request_id="req-x")
    assert not cancellation.is_cancelled()
    assert cancellation.request_id == "req-x"


def test_cancellation_set_is_idempotent() -> None:
    cancellation = StreamCancellation(request_id="req-x")
    cancellation.cancel()
    cancellation.cancel()
    cancellation.cancel()
    assert cancellation.is_cancelled()


@pytest.mark.asyncio
async def test_cancellation_event_unblocks_awaiters() -> None:
    cancellation = StreamCancellation(request_id="req-x")

    async def waiter() -> bool:
        await cancellation.cancelled.wait()
        return True

    task = asyncio.create_task(waiter())
    await asyncio.sleep(0)
    assert not task.done()
    cancellation.cancel()
    result = await task
    assert result is True
