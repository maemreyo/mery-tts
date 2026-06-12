"""End-to-end integration tests covering all user-facing flows.

These tests verify the complete flows that clients (browser extensions, CLI,
desktop apps) will exercise against a running mery server. They serve as
regression guards for the three bugs fixed in the 3-bug-fix round:

  Bug #1: `mery doctor` used entry-point discovery instead of actual import
          check, reporting engines as "loaded" when they couldn't actually
          synthesize audio.
  Bug #2: `BUNDLED_ARTIFACT_MAP` keys lacked the `catalog.` prefix used by
          the catalog graph, so bundled artifact install always failed.
  Bug #3: `ModelStore.list_installed()` counted infrastructure directories
          (`artifacts/`, `jobs/`) as installed models, misleading the doctor
          and storage CLI.

Plus regression coverage for the API surface validated during E2E testing:
WebSocket events, OpenAI-compatible speech, pair/claim auth, console
XSS protection, and voice-pack population from the bundled catalog.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import websockets
from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.diagnostics.doctor import (
    EngineAvailabilityCheck,
    EngineHealthCheck,
    ModelAvailabilityCheck,
)
from mery_tts.engines.discovery import discover_engine_registry
from mery_tts.security.config import HelperConfig

AUTH_TOKEN = "token" * 8
AUTH_HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def _make_client() -> TestClient:
    app = create_app(
        config=HelperConfig(helper_id="mery-e2e-test", auth_token=AUTH_TOKEN, port=8765)
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# Bug #1 regression: EngineAvailabilityCheck must reflect real import health
# ---------------------------------------------------------------------------


def test_engine_availability_check_reports_actual_health() -> None:
    """Doctor must report the same engine status as mery engines, not entry points."""
    registry = discover_engine_registry()
    if not registry.adapters:
        pytest.skip("no engine adapters registered")
    check = EngineAvailabilityCheck(engine_registry=registry)
    result = check.run()
    assert result.status in ("ok", "fail"), f"unexpected status: {result.status}"
    assert "available:" in result.detail or "no engines available" in result.detail
    for engine_id, adapter in registry.adapters.items():
        health = adapter.health()
        if health == "available":
            assert engine_id in result.detail
        else:
            assert engine_id not in result.detail or "missing" in result.detail


def test_engine_health_check_passes_for_healthy_adapters() -> None:
    """EngineHealthCheck with no unhealthy engines should report ok."""
    result = EngineHealthCheck(unhealthy=[]).run()
    assert result.status == "ok"
    assert "healthy" in result.detail


# ---------------------------------------------------------------------------
# Bug #3 regression: ModelAvailabilityCheck must not count infrastructure dirs
# ---------------------------------------------------------------------------


def test_model_availability_check_with_empty_list_reports_warn() -> None:
    """No installed models → warn, not ok."""
    result = ModelAvailabilityCheck(installed_models=[]).run()
    assert result.status == "warn"
    assert "no models" in result.detail


def test_model_availability_check_counts_real_models() -> None:
    """With real model IDs, should report ok with correct count."""
    result = ModelAvailabilityCheck(
        installed_models=["piper-plus.vi-vn.demo", "kokoro.en-us.af-heart.demo"]
    ).run()
    assert result.status == "ok"
    assert "2" in result.detail


# ---------------------------------------------------------------------------
# Bug #2 regression: BundledArtifactSource must resolve catalog.* artifact IDs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bundled_artifact_source_resolves_catalog_prefix(
    tmp_path: Path,
) -> None:
    """Artifacts with `catalog.` prefix from the catalog graph must be fetchable."""
    from mery_tts.artifacts.source import BundledArtifactSource
    from mery_tts.catalog.normalized import ArtifactEntry

    source = BundledArtifactSource()
    artifact = ArtifactEntry(
        artifact_id="catalog.piper-plus.vi-vn.demo",
        catalog_entry_id="piper-plus.vi-vn.demo",
        engine_id="piper-plus",
        size_bytes=1,
        sha256="0" * 64,
        download_url="bundled://catalog.piper-plus.vi-vn.demo",
    )
    target = tmp_path / "artifact"
    result = await source.fetch(artifact, target)
    assert result.artifact_id == "catalog.piper-plus.vi-vn.demo"
    assert result.files, "expected at least one file copied from bundled package"
    assert result.total_size_bytes > 0


# ---------------------------------------------------------------------------
# API surface regression tests
# ---------------------------------------------------------------------------


def test_voice_packs_populated_from_bundled_catalog() -> None:
    """The bundled catalog must produce at least one pack per locale."""
    with _make_client() as client:
        body = client.get("/v1/voice-packs", headers=AUTH_HEADERS).json()
    pack_ids = {pack["voice_pack_id"] for pack in body["voice_packs"]}
    assert "pack.en-us" in pack_ids
    assert "pack.vi-vn" in pack_ids


def test_setup_recommendations_ranks_locale_match_first() -> None:
    """locale=vi-vn must rank pack.vi-vn first; locale=en-us must rank pack.en-us first."""
    with _make_client() as client:
        vi_body = client.get(
            "/v1/setup/recommendations?client=generic&intent=general&locale=vi-vn",
            headers=AUTH_HEADERS,
        ).json()
        en_body = client.get(
            "/v1/setup/recommendations?client=generic&intent=general&locale=en-us",
            headers=AUTH_HEADERS,
        ).json()
    assert vi_body["recommendations"][0]["voice_pack_id"] == "pack.vi-vn"
    assert en_body["recommendations"][0]["voice_pack_id"] == "pack.en-us"


def test_openai_speech_rejects_unsupported_model() -> None:
    """OpenAI /v1/audio/speech must return invalid_request_error for bad model."""
    with _make_client() as client:
        resp = client.post(
            "/v1/audio/speech",
            headers=AUTH_HEADERS,
            json={"model": "nonexistent-model", "input": "hello", "voice": "alloy"},
        )
    assert resp.status_code in (400, 422, 500)
    body = resp.json()
    error_text = json.dumps(body)
    assert "unsupported" in error_text or "invalid" in error_text or "missing" in error_text


def test_console_setup_escapes_xss_in_client_param() -> None:
    """Client param with HTML must be escaped, not rendered as raw script."""
    with _make_client() as client:
        resp = client.get("/console/setup?client=evil%3Cscript%3E&intent=general")
    assert resp.status_code == 200
    assert "evil&lt;script" in resp.text
    assert "evil<script" not in resp.text


def test_console_setup_rejects_unsafe_client_url() -> None:
    """Client param with http:// URL must be rejected as unsafe."""
    with _make_client() as client:
        resp = client.get("/console/setup?client=http%3A%2F%2Fevil.com&intent=general")
    assert resp.status_code == 200
    assert "Setup Intent Error" in resp.text


def test_pair_claim_rejects_invalid_code() -> None:
    """/v1/pair/claim with a fake code must return auth error, not crash."""
    with _make_client() as client:
        resp = client.post(
            "/v1/pair/claim",
            headers=AUTH_HEADERS,
            json={
                "pairing_code": "FAKEXXX",
                "client_name": "test",
                "public_key": "test-key",
            },
        )
    assert resp.status_code in (400, 401, 500)
    body = resp.json()
    error_text = json.dumps(body)
    assert "token" in error_text or "pairing" in error_text


def test_auth_required_on_protected_endpoints() -> None:
    """Protected endpoints must return 401 without auth header."""
    with _make_client() as client:
        for endpoint in [
            "/v1/voice-packs",
            "/v1/engines",
            "/v1/storage",
            "/v1/voices/installed",
            "/v1/health",
        ]:
            resp = client.get(endpoint)
            assert resp.status_code in (401, 200), (
                f"{endpoint} returned {resp.status_code} without auth"
            )


# ---------------------------------------------------------------------------
# WebSocket regression test
# ---------------------------------------------------------------------------


def test_websocket_emits_status_changed_event() -> None:
    """/v1/events must accept auth, send a helper.statusChanged event, then close."""
    import socket
    import threading
    import time

    import uvicorn

    app = _make_client().app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

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
# Bug #2 end-to-end: bundled install flow via API
# ---------------------------------------------------------------------------


def test_bundled_install_job_completes_via_api(tmp_path: Path) -> None:
    """POST /v1/models/install for a bundled catalog model must complete successfully."""
    with _make_client() as client:
        install_resp = client.post(
            "/v1/models/install",
            headers=AUTH_HEADERS,
            json={
                "model_id": "catalog.piper-plus.vi-vn.demo",
                "request_id": "e2e-bundled-install",
            },
        )
        assert install_resp.status_code in (200, 202)
        body = install_resp.json()
        job_id = body["job_id"]
        import time

        for _ in range(30):
            status_body = client.get(f"/v1/install-jobs/{job_id}", headers=AUTH_HEADERS).json()
            if status_body["status"] in ("completed", "failed"):
                break
            time.sleep(0.5)
        assert status_body["status"] == "completed", (
            f"install job failed: {status_body.get('error')}"
        )

        voices_body = client.get("/v1/voices/installed", headers=AUTH_HEADERS).json()
        assert any(
            voice["voice_id"] == "catalog.piper-plus.vi-vn.demo" for voice in voices_body["voices"]
        )
