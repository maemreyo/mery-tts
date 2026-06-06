"""HTTP transport for the OpenAI-compatible raw PCM stream.

ADR-0034: pre-first-byte errors are JSON; post-first-byte failures
terminate and log without JSON wrappers. ``audio/L16`` content type is
derived from the first chunk's metadata.
"""

from mery_tts.streaming.transports.http import (
    HttpStreamHeaders,
    build_audio_l16_content_type,
    build_mery_diagnostic_headers,
    build_openai_pcm_stream_response,
)

__all__ = [
    "HttpStreamHeaders",
    "build_audio_l16_content_type",
    "build_mery_diagnostic_headers",
    "build_openai_pcm_stream_response",
]
