from collections.abc import AsyncIterator

import pytest

from mery_tts.api.orchestration.install import InstallOrchestrator
from mery_tts.api.ws.events import synthesize_events
from mery_tts.engines.base import PCMChunk
from mery_tts.models.events import InstallDone, InstallFailed, InstallProgress


async def install_events() -> AsyncIterator[object]:
    yield InstallProgress(job_id="job", model_id="model", phase="download", percent=50)
    yield InstallDone(job_id="job", model_id="model", engine_id="fake")


@pytest.mark.asyncio
async def test_install_orchestrator_maps_events_and_refreshes_after_done() -> None:
    refreshes: list[str] = []
    emitted = await InstallOrchestrator(
        refresh=lambda: refreshes.append("refresh"),
    ).run(install_events())

    assert [event.event_type for event in emitted] == ["install.progress", "install.completed"]
    assert refreshes == ["refresh"]


@pytest.mark.asyncio
async def test_install_orchestrator_does_not_refresh_on_failure() -> None:
    async def failed() -> AsyncIterator[object]:
        yield InstallFailed(job_id="job", model_id="model", error="failed")

    refreshes: list[str] = []
    emitted = await InstallOrchestrator(refresh=lambda: refreshes.append("refresh")).run(failed())

    assert emitted[0].event_type == "install.failed"
    assert refreshes == []


@pytest.mark.asyncio
async def test_ws_synthesis_events_are_ordered() -> None:
    async def stream() -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=b"a", sample_rate_hz=24_000, channels=1)

    events = [event async for event in synthesize_events("sess", stream())]

    assert [event["event_type"] for event in events] == [
        "synthesize.started",
        "audio.chunk",
        "audio.done",
    ]
