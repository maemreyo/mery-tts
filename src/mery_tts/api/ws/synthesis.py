"""WebSocket synthesis route — /v1/synthesize/stream.

Protocol v1:
  Client → Server (JSON):
    { "voice": str, "text": str, "rate": float, "include_marks": bool }

  Server → Client (JSON events):
    synthesize.started  — { event_type, schema_version, request_id,
                             sample_rate, channels, encoding }
    word_marks          — { event_type, schema_version, request_id,
                             marks: [{char_index, char_length, start_ms, end_ms}] }
                           (only sent when include_marks=true and engine supports it)
    audio.chunk         — { event_type, schema_version, request_id,
                             chunk_index, audio: <base64 pcm_s16le> }
    audio.completed     — { event_type, schema_version, request_id }
    error               — { event_type, schema_version, request_id, code, message }
"""
from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import WebSocket
from starlette import status

from mery_tts.audio.encoder import AudioEncoder
from mery_tts.engines.annotated import AnnotatedSynthesisCapable
from mery_tts.streaming.pipeline import StreamingPipeline
from mery_tts.voice import VoiceRegistry


def _char_index_marks(text: str, speech_marks: list) -> list[dict]:
    result: list[dict] = []
    cursor = 0
    for sm in speech_marks:
        idx = text.find(sm.word, cursor)
        if idx == -1:
            continue
        result.append({
            "char_index": idx,
            "char_length": len(sm.word),
            "start_ms": sm.start_ms,
            "end_ms": sm.end_ms,
        })
        cursor = idx + len(sm.word)
    return result


async def ws_synthesize(
    websocket: WebSocket,
    *,
    voice_registry: VoiceRegistry,
    voice_aliases: dict[str, str],
) -> None:
    """Handle one /v1/synthesize/stream WebSocket session."""
    try:
        req = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    voice_alias: str = req.get("voice", "")
    text: str = req.get("text", "")
    include_marks: bool = bool(req.get("include_marks", False))
    request_id = f"req-{uuid4().hex[:12]}"

    if not voice_alias or not text:
        await websocket.send_json({
            "schema_version": "v1", "request_id": request_id,
            "event_type": "error", "code": "invalid_request",
            "message": "voice and text are required",
        })
        await websocket.close()
        return

    native_voice_id = voice_aliases.get(voice_alias)
    if native_voice_id is None:
        await websocket.send_json({
            "schema_version": "v1", "request_id": request_id,
            "event_type": "error", "code": "voice_not_found",
            "message": f"voice '{voice_alias}' is not installed",
        })
        await websocket.close()
        return

    try:
        adapter, voice = voice_registry.resolve_route(native_voice_id)
    except (KeyError, ValueError) as exc:
        await websocket.send_json({
            "schema_version": "v1", "request_id": request_id,
            "event_type": "error", "code": "voice_not_routable",
            "message": str(exc),
        })
        await websocket.close()
        return

    try:
        if include_marks and isinstance(adapter, AnnotatedSynthesisCapable):
            result = await adapter.synthesize_annotated(text, voice)
            if not result.chunks:
                raise ValueError("synthesize_annotated returned no audio chunks")
            first = result.chunks[0]
            await websocket.send_json({
                "schema_version": "v1", "request_id": request_id,
                "event_type": "synthesize.started",
                "sample_rate": first.sample_rate_hz,
                "channels": first.channels,
                "encoding": first.encoding,
            })
            marks = _char_index_marks(text, result.marks)
            if marks:
                await websocket.send_json({
                    "schema_version": "v1", "request_id": request_id,
                    "event_type": "word_marks",
                    "marks": marks,
                })
            for i, chunk in enumerate(result.chunks):
                await websocket.send_json({
                    "schema_version": "v1", "request_id": request_id,
                    "event_type": "audio.chunk",
                    "chunk_index": i,
                    "audio": AudioEncoder.encode_chunk(chunk),
                })
        else:
            pipeline = StreamingPipeline(
                adapter=adapter,
                voice=voice,
                text=text,
                request_id=request_id,
            )
            first_sent = False
            idx = 0
            async for chunk in pipeline.run():
                if not first_sent:
                    await websocket.send_json({
                        "schema_version": "v1", "request_id": request_id,
                        "event_type": "synthesize.started",
                        "sample_rate": chunk.sample_rate_hz,
                        "channels": chunk.channels,
                        "encoding": chunk.encoding,
                    })
                    first_sent = True
                await websocket.send_json({
                    "schema_version": "v1", "request_id": request_id,
                    "event_type": "audio.chunk",
                    "chunk_index": idx,
                    "audio": AudioEncoder.encode_chunk(chunk),
                })
                idx += 1

        await websocket.send_json({
            "schema_version": "v1", "request_id": request_id,
            "event_type": "audio.completed",
        })
    except Exception as exc:
        try:
            await websocket.send_json({
                "schema_version": "v1", "request_id": request_id,
                "event_type": "error", "code": "synthesis_failed",
                "message": str(exc),
            })
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
