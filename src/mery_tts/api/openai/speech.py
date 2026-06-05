from collections.abc import AsyncIterator

from pydantic import BaseModel, ConfigDict, Field

from mery_tts.voice import VoiceRegistry


class OpenAISpeechRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    input: str = Field(min_length=1)
    response_format: str = "pcm"
    stream: bool = False


def openai_error(message: str, *, status: int = 400) -> tuple[dict[str, dict[str, str]], int]:
    return ({"error": {"message": message, "type": "invalid_request_error"}}, status)


async def synthesize_openai_speech(
    request: OpenAISpeechRequest,
    *,
    voice_registry: VoiceRegistry,
    voice_aliases: dict[str, str],
) -> bytes:
    if request.response_format not in {"pcm", "wav"}:
        raise ValueError("unsupported response_format")
    native_voice_id = voice_aliases.get(request.voice)
    if native_voice_id is None:
        raise KeyError("voice alias is not installed")
    adapter, voice = voice_registry.resolve_route(native_voice_id)
    chunks = [chunk async for chunk in adapter.synthesize(request.input, voice)]
    return b"".join(chunk.pcm for chunk in chunks)


async def iter_openai_pcm(
    request: OpenAISpeechRequest,
    *,
    voice_registry: VoiceRegistry,
    voice_aliases: dict[str, str],
) -> AsyncIterator[bytes]:
    if request.response_format != "pcm":
        raise ValueError("streaming only supports pcm")
    native_voice_id = voice_aliases.get(request.voice)
    if native_voice_id is None:
        raise KeyError("voice alias is not installed")
    adapter, voice = voice_registry.resolve_route(native_voice_id)
    expected: tuple[int, int] | None = None
    async for chunk in adapter.synthesize(request.input, voice):
        metadata = (chunk.sample_rate_hz, chunk.channels)
        if expected is None:
            expected = metadata
        elif expected != metadata:
            raise ValueError("unstable PCM metadata")
        yield chunk.pcm
