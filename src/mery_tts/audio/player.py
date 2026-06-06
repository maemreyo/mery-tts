import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Protocol

from mery_tts.engines.base import PCMChunk
from mery_tts.errors import ErrorCategory, ErrorCode, diagnostic_error


class PlaybackStream(Protocol):
    def write(self, data: bytes) -> None: ...

    def close(self) -> None: ...


StreamFactory = Callable[[int, int], PlaybackStream]


class SoundDeviceStream:
    def __init__(self, *, sample_rate_hz: int, channels: int) -> None:
        import sounddevice

        self._stream = sounddevice.OutputStream(
            samplerate=sample_rate_hz,
            channels=channels,
            dtype="int16",
        )
        self._stream.start()

    def write(self, data: bytes) -> None:
        import numpy as np

        samples = np.frombuffer(data, dtype="<i2")
        self._stream.write(samples)

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()


class AudioPlayer:
    def __init__(
        self,
        *,
        stream_factory: StreamFactory | None = None,
        write: Callable[[PCMChunk], None] | None = None,
    ) -> None:
        self._stream_factory = stream_factory or self._sounddevice_stream
        self._legacy_write = write
        self.stopped = False
        self._active_stream: PlaybackStream | None = None

    async def play(self, stream: AsyncIterator[PCMChunk]) -> None:
        try:
            if self._legacy_write is not None:
                await self._play_legacy(stream)
                return
            await self._play_device(stream)
        except (ImportError, OSError, RuntimeError) as exc:
            raise diagnostic_error(
                code=ErrorCode.PLAYBACK_DEVICE_UNAVAILABLE,
                category=ErrorCategory.PLAYBACK,
                request_id="local",
                diagnostic={"reason": str(exc)},
            ) from exc

    async def _play_legacy(self, stream: AsyncIterator[PCMChunk]) -> None:
        async for chunk in stream:
            if self.stopped:
                break
            if self._legacy_write is not None:
                self._legacy_write(chunk)

    async def _play_device(self, stream: AsyncIterator[PCMChunk]) -> None:
        active_stream: PlaybackStream | None = None
        try:
            async for chunk in stream:
                if self.stopped:
                    break
                if active_stream is None:
                    active_stream = self._stream_factory(chunk.sample_rate_hz, chunk.channels)
                    self._active_stream = active_stream
                await asyncio.to_thread(active_stream.write, chunk.pcm)
        except asyncio.CancelledError:
            self.stop()
            raise
        finally:
            if active_stream is not None:
                await asyncio.to_thread(active_stream.close)
                self._active_stream = None

    def stop(self) -> None:
        self.stopped = True
        if self._active_stream is not None:
            self._active_stream.close()
            self._active_stream = None

    @staticmethod
    def _sounddevice_stream(sample_rate_hz: int, channels: int) -> PlaybackStream:
        return SoundDeviceStream(sample_rate_hz=sample_rate_hz, channels=channels)
