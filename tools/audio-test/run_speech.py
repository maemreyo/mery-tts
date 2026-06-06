#!/usr/bin/env uv run python
"""End-to-end audio test: real Piper-plus / Kokoro synthesis through `mery serve`.

This script is **not** part of the pytest suite — it is a manual real-runtime
smoke test the maintainer runs after installing the matching optional extras
and a real fixture model. The script is deliberately short and reports clear
next steps when the environment is not ready, rather than failing silently.

Usage examples:

    # Default: synthesize a sample phrase, auto-start the server
    uv run python tools/audio-test/run_speech.py

    # Custom text + voice alias + output path
    uv run python tools/audio-test/run_speech.py \\
        --text "Xin chào thế giới" \\
        --voice alloy \\
        --output tools/audio-test/output/vi-hello.wav

    # Connect to an already-running server on a custom port
    uv run python tools/audio-test/run_speech.py \\
        --host 127.0.0.1 --port 18888

Exit codes:
  0  success — WAV file written and validated
  2  optional engine extra not installed (clear remediation printed)
  3  no installed voices (script suggests how to install one)
  4  server unreachable / auth failed
  5  synthesis succeeded but the response bytes do not look like a valid WAV
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHRASE = "Hello from Mery. This is a real engine audio smoke test."
DEFAULT_VOICE = "alloy"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "smoke.wav"

ENGINE_EXTRAS = {
    "piper-plus": "mery-tts-server[piper-plus]",
    "kokoro": "mery-tts-server[kokoro]",
}


def _default_data_dir() -> Path:
    override = os.environ.get("MERY_TTS_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / "Library" / "Application Support" / "Mery TTS"


def log(level: str, message: str) -> None:
    print(f"[{level}] {message}", file=sys.stderr)


def detect_engine_extras() -> list[str]:
    import importlib.util

    found: list[str] = []
    if importlib.util.find_spec("piper") is not None:
        found.append("piper-plus")
    if (
        importlib.util.find_spec("kokoro_onnx") is not None
        or importlib.util.find_spec("kokoro") is not None
    ):
        found.append("kokoro")
    return found


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def read_token(data_dir: Path) -> str:
    config_path = data_dir / "config" / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"config not found at {config_path} — start `mery serve` once to bootstrap it"
        )
    return json.loads(config_path.read_text())["auth_token"]


def http_get_json(url: str, token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post_json(url: str, token: str, body: dict[str, Any]) -> tuple[int, bytes, str]:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() if exc.fp is not None else b"", exc.headers.get("Content-Type", "")


def start_server_if_needed(
    *,
    host: str,
    port: int,
    data_dir: Path,
    log_path: Path,
) -> subprocess.Popen[bytes] | None:
    if port_in_use(host, port):
        log("info", f"server already listening on {host}:{port} — reusing it")
        return None
    env = {
        **os.environ,
        "MERY_TTS_DATA_DIR": str(data_dir),
        "MERY_TTS_PORT": str(port),
        "PATH": os.environ.get("PATH", ""),
    }
    log("info", f"starting `mery serve` on {host}:{port} (data_dir={data_dir})")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("ab")
    proc = subprocess.Popen(
        ["uv", "run", "mery", "serve"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + 15
    while time.time() < deadline:
        if port_in_use(host, port):
            log("info", f"server up (pid={proc.pid}, log={log_path})")
            return proc
        time.sleep(0.25)
    proc.terminate()
    raise RuntimeError(
        f"server did not start within 15s — see {log_path} for the uvicorn output"
    )


def stop_server(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None:
        return
    log("info", f"stopping background server (pid={proc.pid})")
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def pick_voice(installed_voices: list[dict[str, Any]], requested: str) -> str:
    aliases = {voice["voice_id"] for voice in installed_voices}
    aliases_short = {voice["voice_id"].split(".")[-1] for voice in installed_voices}
    if requested in aliases or requested in aliases_short:
        return requested
    if installed_voices:
        first = installed_voices[0]["voice_id"]
        log("warn", f"requested voice {requested!r} not installed — using {first!r} instead")
        return first
    raise LookupError("no installed voices")


def validate_wav(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as fh:
        riff = fh.read(4)
        if riff != b"RIFF":
            raise ValueError(f"file does not start with RIFF magic (got {riff!r})")
        fh.read(4)  # RIFF chunk size, not needed
        wave = fh.read(4)
        if wave != b"WAVE":
            raise ValueError(f"file is not a WAVE container (got {wave!r})")
        fh.read(4)  # 'fmt '
        fmt_size = struct.unpack("<I", fh.read(4))[0]
        if fmt_size < 16:
            raise ValueError(f"unexpected fmt chunk size {fmt_size}")
        audio_format, num_channels, sample_rate = struct.unpack("<HHI", fh.read(8))
        if audio_format != 1:
            raise ValueError(f"expected PCM (audio_format=1), got {audio_format}")
    return num_channels, sample_rate, audio_format


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--text", default=DEFAULT_PHRASE, help="phrase to synthesize")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="voice alias to use (e.g. alloy, catalog.*.*)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="WAV output path")
    parser.add_argument("--host", default="127.0.0.1", help="server host")
    parser.add_argument("--port", type=int, default=18765, help="server port")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_default_data_dir(),
        help="runtime data dir; default follows MERY_TTS_DATA_DIR or the macOS app path",
    )
    parser.add_argument(
        "--keep-server",
        action="store_true",
        help="leave the auto-started `mery serve` running on exit (handy for inspecting the console)",
    )
    args = parser.parse_args()

    extras = detect_engine_extras()
    if not extras:
        log("error", "no optional engine extras detected")
        for engine, extra in ENGINE_EXTRAS.items():
            log("info", f"  install {engine}: uv pip install -e '{extra}'")
        return 2
    log("info", f"engine extras present: {', '.join(extras)}")

    proc: subprocess.Popen[bytes] | None = None
    server_log = args.data_dir / "logs" / "audio-test-server.log"
    try:
        proc = start_server_if_needed(
            host=args.host,
            port=args.port,
            data_dir=args.data_dir,
            log_path=server_log,
        )
        token = read_token(args.data_dir)
    except (FileNotFoundError, RuntimeError) as exc:
        log("error", str(exc))
        return 4

    base_url = f"http://{args.host}:{args.port}"
    try:
        health = http_get_json(f"{base_url}/v1/health", token)
        log("info", f"health: {health.get('status')}")
        voices = http_get_json(f"{base_url}/v1/voices/installed", token)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        log("error", f"auth or transport failure: {exc}")
        stop_server(proc)
        return 4

    installed = voices.get("voices", [])
    if not installed:
        log("error", "no installed voices — install one first:")
        log("info", "  uv run mery models install piper-plus.vi-vn.demo")
        log("info", "  # or any voice from `uv run mery catalog`")
        stop_server(proc)
        return 3
    log("info", f"installed voices: {[v['voice_id'] for v in installed]}")

    chosen = pick_voice(installed, args.voice)
    log("info", f"synthesizing text='{args.text}' voice={chosen} format=wav")
    status, body, content_type = http_post_json(
        f"{base_url}/v1/audio/speech",
        token,
        {
            "model": "tts-1",
            "voice": chosen,
            "input": args.text,
            "response_format": "wav",
            "stream": False,
        },
    )
    if status != 200:
        log("error", f"server returned HTTP {status}: {body[:200]!r} (content-type={content_type})")
        stop_server(proc)
        return 4
    if "audio/wav" not in content_type:
        log("error", f"expected audio/wav content-type, got {content_type!r}")
        stop_server(proc)
        return 5

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(body)
    try:
        channels, sample_rate, _ = validate_wav(args.output)
    except ValueError as exc:
        log("error", f"response is not a valid WAV: {exc}")
        return 5

    log("info", f"wrote {len(body)} bytes to {args.output}")
    log("info", f"  format: PCM {sample_rate} Hz, {channels} channel(s)")
    if shutil.which("afplay"):
        log("info", f"  playback (macOS): afplay {args.output}")
    elif shutil.which("aplay"):
        log("info", f"  playback (Linux): aplay {args.output}")
    elif shutil.which("ffplay"):
        log("info", f"  playback (ffmpeg): ffplay -hide_banner -autoexit {args.output}")

    if not args.keep_server:
        stop_server(proc)
    else:
        log("info", "--keep-server set; leaving `mery serve` running for follow-up tests")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("warn", "interrupted by user")
        raise SystemExit(130)
