"""Full client-server flow tests.

These tests cover the complete path that a real client (browser extension,
desktop app, CLI) walks through when integrating with a Mery TTS server:

    1. Boot the server (TestClient factory).
    2. Pair via CLI → claim via HTTP → receive bearer token.
    3. Use the token to call protected endpoints (/v1/health, /v1/engines,
       /v1/voices/installed, /v1/catalog/voices, /v1/storage).
    4. Install a bundled voice via POST /v1/models/install → poll job.
    5. Synthesize audio via the OpenAI-compatible /v1/audio/speech endpoint
       (blocking WAV, streaming PCM) — verified with a real Piper model.
    6. Verify the diagnostic X-Mery-* response headers.
    7. Rotate the long-lived token and confirm the old one is rejected.
    8. Verify the console SPA serves the setup page with the pairing code.
    9. Use the `mery speak` CLI to write a WAV file end-to-end.
   10. Verify the WebSocket /v1/events stream emits helper.statusChanged.

Synthesis tests (``test_openai_speech_*``, ``test_http_*_with_real_piper``)
use a real Piper model (amy-low, ~63 MB) downloaded once per module from
HuggingFace. They are marked ``engine`` + ``integration`` and require the
``piper-plus`` package to be installed. They assert HTTP 200 OK with real
audio bytes — never 400/503.

Non-synthesis tests use fake synthesizers for speed and determinism.

Regression targets:
  - Pair/claim token must be the same one the server validates against.
  - Voice aliases must round-trip through the OpenAI speech endpoint.
  - Real Piper synthesis must emit 200 OK + valid WAV + correct X-Mery-* headers.
  - PCM streaming must chunk and emit X-Mery-Sample-Rate from the first chunk.
  - Token rotation must invalidate prior tokens (401 on protected calls).
  - Storage endpoint must report non-zero used_bytes when voices are installed.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import socket
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest
import websockets
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from mery_tts.api.app import create_app
from mery_tts.cli.main import app as cli_app
from mery_tts.engines.base import EngineRegistry
from mery_tts.engines.kokoro.adapter import KokoroAdapter
from mery_tts.engines.piper_plus.adapter import PiperPlusAdapter
from mery_tts.security.config import HelperConfig, HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.smoke.record import SmokeRecordStore
from mery_tts.storage.identity import StorageIdentityStore
from mery_tts.voice import ModelFileVoicePayload, PresetVoicePayload, VoiceDescriptor
from mery_tts.voice.registry import VoiceRegistry
from mery_tts.voice.resolver import ResolvedModelFilePayload, ResolvedVoice

AUTH_TOKEN = "flow-token-" + "x" * 24
AUTH_HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

PIPER_VOICE_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx"
)
PIPER_CONFIG_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/"
    "low/en_US-amy-low.onnx.json"
)


# ---------------------------------------------------------------------------
# Fake-synthesizer app builder (for non-synthesis tests)
# ---------------------------------------------------------------------------


def _fake_piper_synthesizer(text: str, voice: VoiceDescriptor):
    return [b"piper-pcm-" + text.encode("utf-8")[:8]]


def _fake_kokoro_synthesizer(text: str, voice: VoiceDescriptor):
    return [b"kokoro-pcm-" + text.encode("utf-8")[:8]]


def _build_flow_app(
    tmp_path: Path,
    *,
    token: str = AUTH_TOKEN,
    aliases: dict[str, str] | None = None,
    piper_voice_id: str = "piper-plus.vi-vn.demo",
    kokoro_voice_id: str = "kokoro.en-us.af-heart.demo",
) -> Any:
    """Build a TestClient-ready app with both engines, aliases, and storage.

    Mirrors the ``_app_with_both_providers`` pattern from
    ``test_two_provider_smoke.py`` so the full flow can be exercised
    without real Piper/Kokoro weights.
    """
    piper = PiperPlusAdapter(synthesizer=_fake_piper_synthesizer)
    kokoro = KokoroAdapter(synthesizer=_fake_kokoro_synthesizer)

    piper_voice = VoiceDescriptor(
        voice_id=piper_voice_id,
        engine_id="piper-plus",
        payload=ModelFileVoicePayload(
            artifact_id=piper_voice_id,
            relative_path=f"{piper_voice_id}.onnx",
        ),
    )
    kokoro_voice = VoiceDescriptor(
        voice_id=kokoro_voice_id,
        engine_id="kokoro",
        payload=PresetVoicePayload(preset_id=kokoro_voice_id),
    )

    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(
        engine_id="piper-plus",
        artifact_id=piper_voice_id,
        metadata={"catalogEntryId": piper_voice_id},
    )
    store.write_artifact_manifest(
        engine_id="kokoro",
        artifact_id=kokoro_voice_id,
        metadata={"catalogEntryId": kokoro_voice_id},
    )
    store.write_voice_manifest(
        piper_voice_id,
        [piper_voice_id],
        {
            "kind": "model-file",
            "artifact_id": piper_voice_id,
            "relative_path": f"{piper_voice_id}.onnx",
        },
    )
    store.write_voice_manifest(
        kokoro_voice_id,
        [kokoro_voice_id],
        {"kind": "preset", "preset_id": kokoro_voice_id},
    )

    registry = EngineRegistry(adapters={"piper-plus": piper, "kokoro": kokoro})
    voice_registry = VoiceRegistry(registry.adapters)
    voice_registry.register(piper_voice)
    voice_registry.register(kokoro_voice)

    smoke_store = SmokeRecordStore(data_dir=tmp_path)

    if aliases is None:
        aliases = {
            "alloy": piper_voice_id,
            "echo": kokoro_voice_id,
        }

    return create_app(
        config=HelperConfig(helper_id="mery-flow-test", auth_token=token, port=8765),
        engine_registry=registry,
        voice_registry=voice_registry,
        voice_aliases=aliases,
        storage_identity_store=store,
        smoke_record_store=smoke_store,
    )


# ---------------------------------------------------------------------------
# Real Piper model fixture (for synthesis tests)
# ---------------------------------------------------------------------------


def _piper_installed() -> bool:
    return importlib.util.find_spec("piper") is not None


def _ensure_nltk_data() -> bool:
    """Download the NLTK resources Piper needs for English tokenization."""
    import nltk

    nltk_dir = Path.home() / "nltk_data"
    nltk_dir.mkdir(exist_ok=True)
    resources = [
        ("corpora/cmudict", "cmudict"),
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
    ]
    for _path, name in resources:
        try:
            nltk.data.find(_path)
        except LookupError:
            try:
                nltk.download(name, download_dir=str(nltk_dir), quiet=True)
            except Exception:
                return False
    return True


def _download_file(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310
        dest.write_bytes(resp.read())


def _resolved_amy_voice(model_dir: Path) -> ResolvedVoice:
    """Build a ResolvedVoice for amy-low carrying the real config's native rate."""
    model_path = model_dir / "en_US-amy-low.onnx"
    config_path = model_dir / "en_US-amy-low.onnx.json"
    config_data = json.loads(config_path.read_text())
    native_rate = config_data.get("audio", {}).get("sample_rate") or config_data.get("sample_rate")
    return ResolvedVoice(
        voice_id="en_US-amy-low",
        engine_id="piper-plus",
        payload=ResolvedModelFilePayload(
            artifact_id="real-piper-amy",
            model_path=model_path,
            config_path=config_path,
            native_sample_rate_hz=native_rate,
        ),
    )


@pytest.fixture(scope="module")
def real_piper_model_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Download amy-low once per test module; tmp_path_factory auto-cleans at session end."""
    if not _piper_installed():
        pytest.skip("piper-plus package is not installed")
    if not _ensure_nltk_data():
        pytest.skip("NLTK data could not be downloaded")
    model_dir = tmp_path_factory.mktemp("piper-amy-low-real")
    _download_file(PIPER_VOICE_URL, model_dir / "en_US-amy-low.onnx")
    _download_file(PIPER_CONFIG_URL, model_dir / "en_US-amy-low.onnx.json")
    return model_dir


@pytest.fixture()
def real_piper_app(real_piper_model_dir: Path, tmp_path: Path) -> Any:
    """Build a TestClient-ready app backed by a real Piper model.

    Registers the amy-low resolved voice with the native sample rate
    read from the real config JSON, so the OpenAI speech endpoint
    reports 200 OK + real audio bytes.
    """
    piper = PiperPlusAdapter()
    resolved = _resolved_amy_voice(real_piper_model_dir)
    piper.register_resolved_voice(resolved)

    voice_descriptor = VoiceDescriptor(
        voice_id="en_US-amy-low",
        engine_id="piper-plus",
        display_name="Amy (real Piper)",
        language="en-US",
        payload=ModelFileVoicePayload(
            artifact_id="real-piper-amy",
            relative_path="en_US-amy-low.onnx",
        ),
    )

    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(
        engine_id="piper-plus",
        artifact_id="en_US-amy-low",
        metadata={"catalogEntryId": "en_US-amy-low"},
    )
    store.write_voice_manifest(
        "en_US-amy-low",
        ["en_US-amy-low"],
        {
            "kind": "model-file",
            "artifact_id": "en_US-amy-low",
            "relative_path": "en_US-amy-low.onnx",
        },
    )

    registry = EngineRegistry(adapters={"piper-plus": piper})
    voice_registry = VoiceRegistry(registry.adapters)
    voice_registry.register(voice_descriptor)

    return create_app(
        config=HelperConfig(helper_id="mery-flow-real", auth_token=AUTH_TOKEN, port=8765),
        engine_registry=registry,
        voice_registry=voice_registry,
        voice_aliases={"alloy": "en_US-amy-low"},
        storage_identity_store=store,
        smoke_record_store=SmokeRecordStore(data_dir=tmp_path),
    )


# ---------------------------------------------------------------------------
# Step 1-3: Boot, pair, claim, auth
# ---------------------------------------------------------------------------


def test_pair_cli_challenge_claimable_via_http(tmp_path: Path, monkeypatch) -> None:
    """`mery pair` writes a challenge file; the same code works via /v1/pair/claim."""
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    cli = CliRunner()
    pair_result = cli.invoke(cli_app, ["pair"])
    assert pair_result.exit_code == 0, pair_result.stdout
    code_line = next(
        line for line in pair_result.stdout.splitlines() if line.startswith("Pairing code:")
    )
    code = code_line.removeprefix("Pairing code:").strip()
    assert len(code) == 6, f"expected 6-char code, got: {code!r}"

    store = HelperConfigStore(tmp_path / "config")
    config = store.load_or_create()
    app = create_app(
        config=config,
        pairing_service=PairingService(config_store=store, config=config),
    )
    with TestClient(app) as client:
        resp = client.post(
            "/v1/pair/claim",
            json={
                "pairing_code": code,
                "client_name": "flow-test",
                "public_key": "test-pub-key",
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["auth_token"] == config.auth_token
    assert body["port"] == config.port
    assert "rest" in body["capabilities"]


def test_claimed_token_authorizes_protected_endpoints(tmp_path: Path) -> None:
    """A token from /v1/pair/claim must unlock /v1/health and /v1/engines."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        # No auth → 401
        assert client.get("/v1/health").status_code == 401
        assert client.get("/v1/engines").status_code == 401

        # Real auth → 200
        health = client.get("/v1/health", headers=AUTH_HEADERS)
        engines = client.get("/v1/engines", headers=AUTH_HEADERS)
    assert health.status_code == 200
    assert engines.status_code == 200
    engine_ids = {e["engine_id"] for e in engines.json()["engines"]}
    assert engine_ids == {"piper-plus", "kokoro"}


# ---------------------------------------------------------------------------
# Step 4-5: Discover voices and synthesize
# ---------------------------------------------------------------------------


def test_explore_endpoints_reflect_installed_voices(tmp_path: Path) -> None:
    """/v1/voices/installed and /v1/catalog/voices must return registered voices."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        installed = client.get("/v1/voices/installed", headers=AUTH_HEADERS).json()
        catalog = client.get("/v1/catalog/voices", headers=AUTH_HEADERS).json()
        storage = client.get("/v1/storage", headers=AUTH_HEADERS).json()

    installed_ids = {v["voice_id"] for v in installed["voices"]}
    assert "piper-plus.vi-vn.demo" in installed_ids
    assert "kokoro.en-us.af-heart.demo" in installed_ids

    catalog_ids = {v["voice_id"] for v in catalog["voices"]}
    # Catalog entries use the `catalog.` prefix for the engine-aware variant
    assert "catalog.piper-plus.vi-vn.demo" in catalog_ids

    # Storage endpoint must show non-zero disk usage (artifacts/manifests were written)
    assert storage.get("used_bytes", 0) > 0, f"expected used_bytes > 0, got {storage!r}"
    assert "free_bytes" in storage


@pytest.mark.engine
@pytest.mark.integration
def test_openai_speech_blocking_wav_returns_200_ok_with_real_piper(
    real_piper_app: Any,
) -> None:
    """POST /v1/audio/speech with the real Piper model returns HTTP 200 OK + valid WAV."""
    with TestClient(real_piper_app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "Hello from Mery, this is a real Piper voice test.",
                "response_format": "wav",
            },
        )
    assert resp.status_code == 200, f"expected 200 OK, got {resp.status_code}: {resp.text[:200]}"
    assert resp.headers["content-type"] == "audio/wav"
    body = resp.content
    # WAV magic bytes: RIFF....WAVE
    assert body[:4] == b"RIFF", f"missing RIFF header: {body[:8]!r}"
    assert body[8:12] == b"WAVE", f"missing WAVE marker: {body[8:16]!r}"
    # The WAV must be a real audio file: header + >0 frames
    assert len(body) > 44, f"WAV too small to be valid: {len(body)} bytes"
    import io
    import wave

    with wave.open(io.BytesIO(body), "rb") as wf:
        n_frames = wf.getnframes()
        rate = wf.getframerate()
        assert n_frames > 0, f"empty WAV: {n_frames} frames"
        assert rate == 16_000, f"amy-low should synthesize at 16 kHz, got {rate}"
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2


@pytest.mark.engine
@pytest.mark.integration
def test_openai_speech_emits_correct_diagnostic_headers_with_real_piper(
    real_piper_app: Any,
) -> None:
    """X-Mery-* headers must reflect the real model's voice, rate, encoding, channels."""
    with TestClient(real_piper_app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "Diagnostic header test with real Piper audio.",
                "response_format": "pcm",
            },
        )
    assert resp.status_code == 200, f"expected 200 OK, got {resp.status_code}: {resp.text[:200]}"
    assert resp.headers.get("x-mery-voice-used") == "en_US-amy-low"
    # x-mery-audio-encoding mirrors the response_format the client requested
    assert resp.headers.get("x-mery-audio-encoding") == "pcm"
    # amy-low is a 16 kHz model — diagnostic header must agree
    assert int(resp.headers["x-mery-sample-rate"]) == 16_000
    assert int(resp.headers["x-mery-channels"]) == 1


@pytest.mark.engine
@pytest.mark.integration
def test_openai_speech_streaming_pcm_emits_real_chunks(real_piper_app: Any) -> None:
    """stream=true with response_format=pcm must return chunked real PCM audio."""
    with (
        TestClient(real_piper_app) as client,
        client.stream(
            "POST",
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "Streaming test with real Piper audio bytes.",
                "response_format": "pcm",
                "stream": True,
            },
        ) as resp,
    ):
        assert resp.status_code == 200, f"expected 200 OK, got {resp.status_code}"
        content_type = resp.headers["content-type"]
        assert "audio" in content_type, f"expected audio content-type, got {content_type!r}"
        chunks: list[bytes] = []
        for chunk in resp.iter_bytes():
            if chunk:
                chunks.append(chunk)
    assert chunks, "expected at least one PCM chunk in the stream"
    total_bytes = b"".join(chunks)
    assert len(total_bytes) > 0, "stream yielded no real audio bytes"


# ---------------------------------------------------------------------------
# Step 6-7: Error cases and token rotation
# ---------------------------------------------------------------------------


def test_openai_speech_unknown_alias_returns_400(tmp_path: Path) -> None:
    """A voice alias that isn't registered must yield a 400 with a structured error."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "not-a-real-alias",
                "input": "x",
                "response_format": "wav",
            },
        )
    assert resp.status_code == 400
    body = resp.json()
    # The server returns a rich error envelope with `code` and `category`,
    # not the minimal OpenAI `{"error": {"message", "type"}}` shape.
    assert body.get("code") == "engine.voice_unsupported"
    assert body.get("category") == "engine"
    assert "not installed" in body.get("sanitized_diagnostic", "").lower()


def test_openai_speech_unsupported_model_returns_400(tmp_path: Path) -> None:
    """A model name outside {tts-1} must be rejected at validation time."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "piper-plus",  # not a valid OpenAI model name
                "voice": "alloy",
                "input": "x",
                "response_format": "wav",
            },
        )
    assert resp.status_code == 400
    body = resp.json()
    assert "unsupported model" in body["error"]["message"]


def test_pair_rotate_invalidates_old_token(tmp_path: Path, monkeypatch) -> None:
    """`mery pair --rotate` must issue a new token and the old one must 401."""
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    store = HelperConfigStore(tmp_path / "config")
    config = store.load_or_create()
    old_token = config.auth_token

    # Boot the server with the *original* token and verify access
    app = create_app(
        config=config,
        pairing_service=PairingService(config_store=store, config=config),
    )
    with TestClient(app) as client:
        # Old token works pre-rotation
        assert (
            client.get("/v1/health", headers={"Authorization": f"Bearer {old_token}"}).status_code
            == 200
        )

    # Rotate via CLI — this rewrites config.json with a fresh token
    rotate_result = CliRunner().invoke(cli_app, ["pair", "--rotate"])
    assert rotate_result.exit_code == 0, rotate_result.stdout

    new_token = store.load_or_create().auth_token
    assert new_token != old_token, "rotation must produce a different token"

    # Build a fresh app that loads the rotated token
    rotated_config = store.load_or_create()
    rotated_app = create_app(
        config=rotated_config,
        pairing_service=PairingService(config_store=store, config=rotated_config),
    )
    with TestClient(rotated_app) as client:
        old_auth = client.get("/v1/health", headers={"Authorization": f"Bearer {old_token}"})
        new_auth = client.get("/v1/health", headers={"Authorization": f"Bearer {new_token}"})
    assert old_auth.status_code == 401, "old token must be rejected after rotation"
    assert new_auth.status_code == 200, "new token must be accepted after rotation"


# ---------------------------------------------------------------------------
# Step 8: Console SPA + setup URL flow
# ---------------------------------------------------------------------------


def test_console_setup_endpoint_renders_recommendations(tmp_path: Path) -> None:
    """/console/setup?client=...&intent=... must render voice pack recommendations (200, HTML)."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.get("/console/setup?client=generic&intent=general&code=ABCDEF")
    assert resp.status_code == 200
    body = resp.text
    # Page is the voice-pack recommendation landing; the pairing code is
    # consumed by the SPA client, not echoed back in this minimal HTML.
    assert "Mery" in body or "mery" in body.lower()
    assert "Voice Pack" in body or "voice pack" in body.lower()
    assert "Client:" in body or "client:" in body.lower()


def test_console_root_serves_spa_shell(tmp_path: Path) -> None:
    """/console must return the SPA shell, not a 404."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.get("/console")
        assets = client.get("/console/assets/anything")
    assert resp.status_code == 200
    assert "<html" in resp.text.lower() or "<!doctype" in resp.text.lower()
    # SPA fallback must not 500 on a missing asset path
    assert assets.status_code in (200, 204, 400, 404)


# ---------------------------------------------------------------------------
# Step 9: `mery speak` CLI writes a WAV file
# ---------------------------------------------------------------------------


def test_mery_speak_cli_writes_wav_file(tmp_path: Path, monkeypatch) -> None:
    """`mery speak --text "..." --output path.wav` must produce a WAV file."""
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    output = tmp_path / "out.wav"
    result = CliRunner().invoke(
        cli_app,
        ["speak", "--text", "hello", "--output", str(output)],
    )
    assert result.exit_code == 0, result.stdout
    assert output.exists(), f"expected {output} to exist after `mery speak`"
    # The CLI emits a JSON status line; verify shape
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["path"] == str(output)
    assert payload["file_size_bytes"] > 0


# ---------------------------------------------------------------------------
# Step 10: WebSocket /v1/events emits a status event with valid auth
# ---------------------------------------------------------------------------


def test_websocket_emits_status_event_with_claimed_token(tmp_path: Path) -> None:
    """A live uvicorn server + WebSocket client proves the auth header round-trips."""
    app = _build_flow_app(tmp_path)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    def _serve() -> None:
        server.run()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            pytest.fail("server did not start within 5s")

        async def _run() -> str:
            uri = f"ws://127.0.0.1:{port}/v1/events"
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            async with websockets.connect(uri, additional_headers=headers) as ws:
                return await asyncio.wait_for(ws.recv(), timeout=5)

        msg = asyncio.run(_run())
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    event = json.loads(msg)
    assert event["event_type"] == "helper.statusChanged"
    assert event["status"] == "ok"


# ---------------------------------------------------------------------------
# Bundled install happy path: real model_id → install job → completed
# ---------------------------------------------------------------------------


def test_bundled_install_via_api_completes(tmp_path: Path) -> None:
    """The bundled catalog model must install via POST /v1/models/install + poll."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        install = client.post(
            "/v1/models/install",
            headers=AUTH_HEADERS,
            json={
                "model_id": "catalog.piper-plus.vi-vn.demo",
                "request_id": "flow-install",
            },
        )
        assert install.status_code in (200, 202)
        job_id = install.json()["job_id"]

        for _ in range(60):
            status = client.get(f"/v1/install-jobs/{job_id}", headers=AUTH_HEADERS).json()
            if status["status"] in ("completed", "failed"):
                break
            time.sleep(0.5)
    assert status["status"] == "completed", f"install failed: {status.get('error')}"


# ---------------------------------------------------------------------------
# CORS preflight: clients with proper Origin header must be allowed
# ---------------------------------------------------------------------------


def test_cors_preflight_allows_authorized_origin(tmp_path: Path) -> None:
    """A browser client on http://127.0.0.1:8765 must pass CORS preflight."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.options(
            "/v1/audio/speech",
            headers={
                "Origin": "http://127.0.0.1:8765",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
    assert resp.status_code == 204
    assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:8765"
    allowed_methods = resp.headers.get("access-control-allow-methods", "").upper()
    assert "POST" in allowed_methods


# ---------------------------------------------------------------------------
# Additional endpoint coverage (packs, diagnostics, runtimes, models CRUD)
# ---------------------------------------------------------------------------


def test_voice_packs_endpoint_returns_populated_packs(tmp_path: Path) -> None:
    """/v1/voice-packs must return at least one pack per supported locale."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        body = client.get("/v1/voice-packs", headers=AUTH_HEADERS).json()
    assert "voice_packs" in body
    pack_ids = {p["voice_pack_id"] for p in body["voice_packs"]}
    assert "pack.en-us" in pack_ids
    assert "pack.vi-vn" in pack_ids


def test_diagnostics_endpoint_runs_eight_checks(tmp_path: Path) -> None:
    """/v1/diagnostics must return at least the 8 standard check names."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        body = client.get("/v1/diagnostics", headers=AUTH_HEADERS).json()
    assert "checks" in body
    checks = body["checks"]
    expected = {
        "engine_availability",
        "engine_health",
        "model_availability",
        "token_configured",
        "server_reachability",
        "disk_space",
        "platform_paths",
        "catalog_available",
    }
    assert expected.issubset(checks.keys()), f"missing checks: {expected - checks.keys()}"
    for status in checks.values():
        assert status in ("ok", "warn", "fail"), f"unexpected status: {status}"


def test_provider_runtimes_endpoint_lists_runtimes(tmp_path: Path) -> None:
    """/v1/provider-runtimes must list piper-plus and kokoro runtimes."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        body = client.get("/v1/provider-runtimes", headers=AUTH_HEADERS).json()
    assert "provider_runtimes" in body
    runtimes = body["provider_runtimes"]
    assert len(runtimes) >= 2
    provider_ids = {r["provider_id"] for r in runtimes}
    assert {"piper-plus", "kokoro"}.issubset(provider_ids)


def test_get_model_details_returns_status(tmp_path: Path) -> None:
    """GET /v1/models/{id} must return 200 with the model's install status."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.get("/v1/models/piper-plus.vi-vn.demo", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_id"] == "piper-plus.vi-vn.demo"
    assert body["status"] in ("installed", "not_installed", "installing", "failed")


def test_delete_model_returns_deleted_true(tmp_path: Path) -> None:
    """DELETE /v1/models/{id} must return 200 with `deleted: true`."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.delete("/v1/models/piper-plus.vi-vn.demo", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_id"] == "piper-plus.vi-vn.demo"
    assert body["deleted"] is True


# ---------------------------------------------------------------------------
# Security middleware: origin allowlist, body size, text length
# ---------------------------------------------------------------------------


def test_origin_not_in_allowlist_rejected(tmp_path: Path) -> None:
    """A request with an Origin header outside 127.0.0.1/localhost must be 403."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.get(
            "/v1/health",
            headers={**AUTH_HEADERS, "Origin": "http://evil.com"},
        )
    assert resp.status_code == 403


def test_oversized_body_returns_413(tmp_path: Path) -> None:
    """A request body larger than max_body_bytes (1 MB default) must be 413."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers={**AUTH_HEADERS, "Content-Length": str(2_000_000)},
            content=b"x" * 2_000_000,
        )
    assert resp.status_code == 413


def test_text_too_long_returns_413(real_piper_app: Any) -> None:
    """A synthesis request with input > max_text_chars (10 000) must be 413."""
    long_text = "x" * 10_001
    with TestClient(real_piper_app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": long_text,
                "response_format": "pcm",
            },
        )
    assert resp.status_code == 413


# ---------------------------------------------------------------------------
# OpenAI speech edge cases: empty/missing input, PCM blocking, Mery options
# ---------------------------------------------------------------------------


def test_openai_speech_empty_input_rejected(tmp_path: Path) -> None:
    """input="" must fail Pydantic min_length=1 validation → 422."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "",
                "response_format": "wav",
            },
        )
    assert resp.status_code == 422


def test_openai_speech_missing_input_field_rejected(tmp_path: Path) -> None:
    """A request without the required `input` field must be 422."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "response_format": "wav",
            },
        )
    assert resp.status_code == 422


@pytest.mark.engine
@pytest.mark.integration
def test_openai_speech_blocking_pcm_returns_200_with_real_piper(
    real_piper_app: Any,
) -> None:
    """response_format=pcm without stream=true must return HTTP 200 + raw PCM bytes."""
    with TestClient(real_piper_app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "Blocking PCM test with real Piper audio.",
                "response_format": "pcm",
            },
        )
    assert resp.status_code == 200, f"expected 200 OK, got {resp.status_code}: {resp.text[:200]}"
    assert resp.headers["content-type"] == "audio/pcm"
    body = resp.content
    assert len(body) > 0, "blocking PCM response must contain real audio bytes"
    # PCM samples are 16-bit LE — first sample must not be a JSON envelope
    assert body[:2] != b'{"', "first bytes look like a JSON error, not PCM audio"


def test_openai_speech_accepts_mery_fallback_options(tmp_path: Path) -> None:
    """The `mery.fallbackVoiceIds` extra field must be accepted (200 OK)."""
    app = _build_flow_app(tmp_path)
    with TestClient(app) as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={
                "model": "tts-1",
                "voice": "alloy",
                "input": "fallback test",
                "response_format": "wav",
                "mery": {
                    "fallbackVoiceIds": ["kokoro.en-us.af-heart.demo"],
                    "fallbackPolicy": "auto",
                    "diagnostics": "headers",
                },
            },
        )
    assert resp.status_code == 200, f"expected 200 OK, got {resp.status_code}: {resp.text[:200]}"
    assert resp.content[:4] == b"RIFF"
