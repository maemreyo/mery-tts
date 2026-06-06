"""Minimal Python client for the Mery OpenAI-compatible raw PCM stream.

Streams a synthesis request to a WAV file. Uses only the Python standard
library — no third-party dependencies required.

Usage:
    python python_client.py \
        --url http://127.0.0.1:8765 \
        --token <auth_token> \
        --model kokoro \
        --voice af_heart \
        --text "Streaming raw PCM is fast and boring." \
        --output out.wav
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StreamFormat:
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int

    @classmethod
    def from_content_type(cls, content_type: str) -> "StreamFormat":
        match = re.match(
            r"audio/L16;rate=(\d+);channels=(\d+)", content_type.strip()
        )
        if match is None:
            raise ValueError(
                f"unsupported Content-Type for raw PCM: {content_type!r}"
            )
        return cls(
            sample_rate_hz=int(match.group(1)),
            channels=int(match.group(2)),
            sample_width_bytes=2,
        )


def fetch_voice_streaming_capability(
    *,
    base_url: str,
    token: str,
    voice_id: str,
) -> dict | None:
    """Return the streaming capability block for an installed voice, or None."""
    request = urllib.request.Request(
        url=f"{base_url}/v1/voices/installed",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    for voice in payload.get("voices", []):
        if voice.get("voice_id") == voice_id:
            return voice.get("streaming")
    return None


def stream_speech_to_wav(
    *,
    base_url: str,
    token: str,
    model: str,
    voice: str,
    text: str,
    output_path: str,
) -> StreamFormat:
    """Stream a raw PCM synthesis to a WAV file. Returns the parsed format."""
    body = json.dumps(
        {
            "model": model,
            "voice": voice,
            "input": text,
            "response_format": "pcm",
            "stream_format": "pcm",
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url=f"{base_url}/v1/audio/speech",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        response = urllib.request.urlopen(request, timeout=30)
    except urllib.error.HTTPError as exc:
        # Pre-first-byte errors come back as JSON.
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"code": "unknown", "sanitized_diagnostic": raw}
        raise SystemExit(
            f"synthesis rejected ({exc.code}): "
            f"{payload.get('code', 'unknown')}: "
            f"{payload.get('sanitized_diagnostic', '')}"
        ) from exc

    content_type = response.headers.get("Content-Type", "")
    fmt = StreamFormat.from_content_type(content_type)
    request_id = response.headers.get("X-Mery-Request-Id", "<unknown>")
    encoding = response.headers.get("X-Mery-Audio-Encoding", "<unknown>")

    print(
        f"streaming: content_type={content_type} "
        f"request_id={request_id} encoding={encoding} "
        f"sample_rate={fmt.sample_rate_hz} channels={fmt.channels}",
        file=sys.stderr,
    )

    with wave.open(output_path, "wb") as wav:
        wav.setnchannels(fmt.channels)
        wav.setsampwidth(fmt.sample_width_bytes)
        wav.setframerate(fmt.sample_rate_hz)
        while True:
            chunk = response.read(4096)
            if not chunk:
                break
            wav.writeframes(chunk)

    return fmt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--token", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", default="out.wav")
    args = parser.parse_args()

    capability = fetch_voice_streaming_capability(
        base_url=args.url,
        token=args.token,
        voice_id=args.voice,
    )
    if capability is None:
        print(
            f"voice {args.voice!r} is not installed", file=sys.stderr
        )
        return 2
    if not capability.get("supported", False):
        print(
            f"voice {args.voice!r} does not support streaming in P1",
            file=sys.stderr,
        )
        return 2

    fmt = stream_speech_to_wav(
        base_url=args.url,
        token=args.token,
        model=args.model,
        voice=args.voice,
        text=args.text,
        output_path=args.output,
    )
    print(
        f"wrote {args.output}: {fmt.sample_rate_hz} Hz, "
        f"{fmt.channels}ch, {fmt.sample_width_bytes * 8}-bit"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
