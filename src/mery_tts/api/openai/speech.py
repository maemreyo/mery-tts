"""OpenAI-compatible speech layer.

ADR-0014: thin OpenAI-compatible route shape. The blocking path
preserves the legacy ``synthesize_openai_speech`` function for
non-streaming callers. The streaming path delegates to the standalone
streaming subsystem (ADR-0031) and emits ``audio/L16`` semantics
(ADR-0034) with first-chunk-derived headers.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from mery_tts.audio.encoder import encode_wav
from mery_tts.streaming.config import StreamingConfig
from mery_tts.streaming.metadata import StreamMetadataError
from mery_tts.streaming.pipeline import StreamingPipeline
from mery_tts.streaming.transports.http import build_openai_pcm_stream_response
from mery_tts.voice import VoiceRegistry

SUPPORTED_OPENAI_MODELS = frozenset({"tts-1"})


class OpenAISpeechRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    model: str = Field(min_length=1)
    voice: str = Field(min_length=1)
    input: str = Field(min_length=1)
    response_format: str = "pcm"
    stream: bool = False


def openai_error(message: str, *, status: int = 400) -> tuple[dict[str, dict[str, str]], int]:
    return ({"error": {"message": message, "type": "invalid_request_error"}}, status)


def validate_openai_model(model: str) -> None:
    if model not in SUPPORTED_OPENAI_MODELS:
        raise ValueError("unsupported model")


async def synthesize_openai_speech(
    request: OpenAISpeechRequest,
    *,
    voice_registry: VoiceRegistry,
    voice_aliases: dict[str, str],
) -> bytes:
    validate_openai_model(request.model)
    if request.response_format not in {"pcm", "wav"}:
        raise ValueError("unsupported response_format")
    native_voice_id = voice_aliases.get(request.voice)
    if native_voice_id is None:
        raise KeyError("voice alias is not installed")
    adapter, voice = voice_registry.resolve_route(native_voice_id)
    chunks = [chunk async for chunk in adapter.synthesize(request.input, voice)]
    if request.response_format == "wav":
        return encode_wav(chunks)
    return b"".join(chunk.pcm for chunk in chunks)


def resolve_openai_streaming_request(
    request: OpenAISpeechRequest,
    *,
    voice_registry: VoiceRegistry,
    voice_aliases: dict[str, str],
) -> tuple[OpenAISpeechRequest, str, StreamingPipeline]:
    """Validate the streaming request and build the streaming pipeline.

    Returns the validated request, the resolved native voice id, and the
    streaming pipeline. The route is responsible for wrapping the
    pipeline's byte iterator into the final ``StreamingResponse``.
    """
    validate_openai_model(request.model)
    if request.response_format != "pcm":
        raise ValueError("streaming only supports pcm")
    native_voice_id = voice_aliases.get(request.voice)
    if native_voice_id is None:
        raise KeyError("voice alias is not installed")
    adapter, voice = voice_registry.resolve_route(native_voice_id)
    request_id = f"req-{uuid4().hex[:12]}"
    pipeline = StreamingPipeline(
        adapter=adapter,
        voice=voice,
        text=request.input,
        request_id=request_id,
    )
    return request, native_voice_id, pipeline


async def build_openai_streaming_response(
    *,
    pipeline: StreamingPipeline,
    config: StreamingConfig,
) -> StreamingResponse | JSONResponse:
    """Build the OpenAI streaming response for ``/v1/audio/speech``.

    Returns a JSON response for pre-first-byte errors (no body bytes
    sent yet), or a ``StreamingResponse`` once the first chunk has been
    validated and headers derived.
    """
    try:
        byte_stream, headers = await build_openai_pcm_stream_response(
            pipeline=pipeline, config=config
        )
    except StreamMetadataError as exc:
        return JSONResponse(
            {"error": {"message": str(exc), "type": "invalid_request_error"}},
            status_code=400,
        )
    except TimeoutError:
        return JSONResponse(
            {
                "error": {
                    "message": "first chunk fetch timed out",
                    "type": "invalid_request_error",
                }
            },
            status_code=504,
        )

    return StreamingResponse(
        byte_stream,
        media_type=headers.content_type,
        headers=headers.extra,
    )


# Kept for callers that need the legacy byte iterator. The route
# delegates to ``build_openai_streaming_response`` instead.
async def iter_openai_pcm(
    request: OpenAISpeechRequest,
    *,
    voice_registry: VoiceRegistry,
    voice_aliases: dict[str, str],
) -> AsyncIterator[bytes]:
    validate_openai_model(request.model)
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
            raise StreamMetadataError("unstable PCM metadata")
        yield chunk.pcm
