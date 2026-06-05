from collections.abc import AsyncIterator, Callable

from mery_tts.engines.base import PCMChunk


class AudioPlayer:
    def __init__(self, *, write: Callable[[PCMChunk], None]) -> None:
        self._write = write
        self.stopped = False

    async def play(self, stream: AsyncIterator[PCMChunk]) -> None:
        async for chunk in stream:
            if self.stopped:
                break
            self._write(chunk)

    def stop(self) -> None:
        self.stopped = True
