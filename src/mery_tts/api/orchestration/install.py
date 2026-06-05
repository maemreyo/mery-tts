from collections.abc import AsyncIterator, Callable

from mery_tts.models.events import InstallDone, InstallFailed, InstallProgress
from mery_tts.schemas.v1 import InstallEvent as InstallSchemaEvent


class InstallOrchestrator:
    def __init__(self, *, refresh: Callable[[], None]) -> None:
        self._refresh = refresh

    async def run(self, events: AsyncIterator[object]) -> list[InstallSchemaEvent]:
        emitted: list[InstallSchemaEvent] = []
        async for event in events:
            if isinstance(event, InstallProgress):
                emitted.append(
                    InstallSchemaEvent(
                        event_type="install.progress",
                        request_id="local",
                        job_id=event.job_id,
                    )
                )
            elif isinstance(event, InstallDone):
                emitted.append(
                    InstallSchemaEvent(
                        event_type="install.completed",
                        request_id="local",
                        job_id=event.job_id,
                    )
                )
                self._refresh()
            elif isinstance(event, InstallFailed):
                emitted.append(
                    InstallSchemaEvent(
                        event_type="install.failed",
                        request_id="local",
                        job_id=event.job_id,
                    )
                )
        return emitted
