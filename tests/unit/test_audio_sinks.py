import base64
import math
import wave
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from mery_tts.audio.encoder import AudioEncoder
from mery_tts.audio.exporter import AudioExporter
from mery_tts.audio.player import AudioPlayer
from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.errors import ErrorCode, FallbackPolicy, LocalTTSError, RecommendedAction
from mery_tts.voice.descriptor import PresetVoicePayload, VoiceDescriptor


def fake_sine_pcm_bytes(samples: int = 6) -> bytes:
    amplitude = 8_000
    sample_rate_hz = 24_000
    frequency_hz = 440
    values = (
        int(amplitude * math.sin(2 * math.pi * frequency_hz * index / sample_rate_hz))
        for index in range(samples)
    )
    return b"".join(value.to_bytes(2, "little", signed=True) for value in values)


class FakePlaybackStream:
    def __init__(self) -> None:
        self.writes: list[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    def close(self) -> None:
        self.closed = True


class FakeEngineAdapter(EngineAdapter):
    engine_id = "fake-sine"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        _ = text
        _ = voice
        sine = fake_sine_pcm_bytes()
        yield PCMChunk(pcm=sine[:6], sample_rate_hz=24_000, channels=1)
        yield PCMChunk(pcm=sine[6:], sample_rate_hz=24_000, channels=1)


def fake_voice() -> VoiceDescriptor:
    return VoiceDescriptor(
        voice_id="fake-sine.en",
        engine_id=FakeEngineAdapter.engine_id,
        payload=PresetVoicePayload(preset_id="fake-sine"),
    )


def fake_stream() -> AsyncIterator[PCMChunk]:
    return FakeEngineAdapter().synthesize("hello", voice=fake_voice())


@pytest.mark.asyncio
async def test_audio_player_drains_stream_and_stops() -> None:
    opened: list[tuple[int, int]] = []
    playback = FakePlaybackStream()
    player = AudioPlayer(
        stream_factory=lambda sample_rate_hz, channels: (
            opened.append((sample_rate_hz, channels)),
            playback,
        )[1]
    )

    await player.play(fake_stream())
    player.stop()

    sine = fake_sine_pcm_bytes()

    assert opened == [(24_000, 1)]
    assert playback.writes == [sine[:6], sine[6:]]
    assert playback.closed is True
    assert player.stopped is True


@pytest.mark.asyncio
async def test_audio_player_stop_prevents_later_chunks_from_writing() -> None:
    playback = FakePlaybackStream()
    player = AudioPlayer(stream_factory=lambda sample_rate_hz, channels: playback)

    original_write = playback.write

    def write_and_stop(data: bytes) -> None:
        original_write(data)
        player.stop()

    playback.write = write_and_stop

    await player.play(fake_stream())

    assert playback.writes == [fake_sine_pcm_bytes()[:6]]
    assert playback.closed is True
    assert player.stopped is True


@pytest.mark.asyncio
async def test_audio_player_closes_stream_on_cancellation() -> None:
    playback = FakePlaybackStream()
    player = AudioPlayer(stream_factory=lambda sample_rate_hz, channels: playback)

    async def cancelling_stream() -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=b"a", sample_rate_hz=24_000, channels=1)
        raise asyncio.CancelledError

    import asyncio

    with pytest.raises(asyncio.CancelledError):
        await player.play(cancelling_stream())

    assert playback.writes == [b"a"]
    assert playback.closed is True
    assert player.stopped is True


@pytest.mark.asyncio
async def test_audio_player_maps_device_failure_to_structured_error() -> None:
    def fail_open(sample_rate_hz: int, channels: int) -> FakePlaybackStream:
        _ = sample_rate_hz, channels
        raise RuntimeError("device unavailable: /Users/private/speaker")

    player = AudioPlayer(stream_factory=fail_open)

    with pytest.raises(LocalTTSError) as error:
        await player.play(fake_stream())

    assert error.value.code == ErrorCode.PLAYBACK_DEVICE_UNAVAILABLE
    assert error.value.recommended_action == RecommendedAction.CHECK_ENGINE
    assert error.value.fallback_policy == FallbackPolicy.USE_CACHED_AUDIO
    assert "/Users" not in error.value.sanitized_diagnostic


@pytest.mark.engine
@pytest.mark.asyncio
async def test_audio_player_real_device_smoke_is_marked_and_skipped_by_default() -> None:
    pytest.skip("manual audio-device smoke: requires local speakers and user opt-in")


def test_audio_encoder_round_trips_pcm_bytes() -> None:
    chunk = PCMChunk(pcm=fake_sine_pcm_bytes(), sample_rate_hz=24_000, channels=1)

    encoded = AudioEncoder.encode_chunk(chunk)

    assert base64.b64decode(encoded) == fake_sine_pcm_bytes()


@pytest.mark.asyncio
async def test_audio_exporter_writes_valid_wav_with_result_metadata(tmp_path: Path) -> None:
    output_path = tmp_path / "hello.wav"

    result = await AudioExporter().export(fake_stream(), output_path)

    assert result.path == output_path
    assert result.file_size_bytes == output_path.stat().st_size
    assert result.duration_seconds == pytest.approx(12 / 2 / 24_000)
    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 24_000
        assert wav_file.readframes(6) == fake_sine_pcm_bytes()


@pytest.mark.asyncio
async def test_audio_exporter_maps_unsupported_format_to_structured_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(LocalTTSError) as error:
        await AudioExporter().export(fake_stream(), tmp_path / "hello.flac")

    assert error.value.code == ErrorCode.SYNTHESIS_UNSUPPORTED_FORMAT
    assert error.value.recommended_action == RecommendedAction.NONE
    assert error.value.fallback_policy == FallbackPolicy.NONE
    assert error.value.sanitized_diagnostic == "export_format=.flac"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        OSError("disk full: /Users/private/path"),
        PermissionError("permission denied: /Users/private/hello.wav"),
    ],
)
async def test_audio_exporter_maps_write_failure_to_structured_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: OSError,
) -> None:
    def fail_write_bytes(path: Path, data: bytes) -> int:
        _ = path
        _ = data
        raise failure

    monkeypatch.setattr(Path, "write_bytes", fail_write_bytes)

    with pytest.raises(LocalTTSError) as error:
        await AudioExporter().export(fake_stream(), tmp_path / "hello.wav")

    assert error.value.code == ErrorCode.STORAGE_WRITE_FAILED
    assert error.value.recommended_action == RecommendedAction.FREE_SPACE
    assert error.value.fallback_policy == FallbackPolicy.NONE
    assert "export_path=hello.wav" in error.value.sanitized_diagnostic
    assert "/Users" not in error.value.sanitized_diagnostic
