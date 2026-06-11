from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from typer.testing import CliRunner

from mery_tts.api.app import create_app, is_allowed_origin
from mery_tts.cli.main import app as cli_app
from mery_tts.diagnostics.history import DiagnosticsEvent, DiagnosticsEventStore
from mery_tts.security.config import HelperConfig, HelperConfigStore


def test_app_factory_builds_without_engines_or_models() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="token" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get("/v1/health", headers={"Authorization": "Bearer " + "token" * 8})

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "v1"
    assert body["status"] in {"ok", "degraded", "unavailable", "ready", "unpaired", "incompatible"}
    assert "helper_id" in body
    assert "helper_version" in body
    assert "contract_version" in body
    assert "engines" in body
    assert "total_usable_voices" in body
    assert "total_installed_voices" in body
    for engine in body["engines"]:
        assert engine["backend_selection"]["supported_backends"] == ["cpu"]
        assert engine["backend_selection"]["selected_backend"] == "cpu"
        assert engine["backend_selection"]["missing_extras"] == []


def test_console_origin_v1_requests_are_normal_clients_and_require_auth() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    origin_headers = {"Origin": "http://127.0.0.1:8765"}
    auth_headers = {
        "Origin": "http://127.0.0.1:8765",
        "Authorization": "Bearer " + "secret" * 8,
    }

    with TestClient(app) as client:
        unauth_health = client.get("/v1/health", headers=origin_headers)
        unauth_install = client.post(
            "/v1/models/install",
            headers=origin_headers,
            json={"schema_version": "v1", "request_id": "console", "model_id": "pack.en-us"},
        )
        authed_health = client.get("/v1/health", headers=auth_headers)
        setup = client.get("/console/setup?client=generic&intent=general&code=ABCDEF")

    assert unauth_health.status_code == 401
    assert unauth_health.json()["code"] == "auth.token_missing"
    assert unauth_install.status_code == 401
    assert unauth_install.json()["code"] == "auth.token_missing"
    assert authed_health.status_code == 200
    assert setup.status_code == 200
    assert "Open Mery Console" in setup.text


def test_console_static_routes_are_public_spa_without_affecting_v1_auth() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        console = client.get("/console")
        fallback = client.get("/console/catalog/deep-link")
        script = client.get("/console/assets/app.js")
        styles = client.get("/console/assets/app.css")
        missing_asset = client.get("/console/assets/missing.js")
        traversal_asset = client.get("/console/assets/%2e%2e/index.html")
        v1_missing = client.get("/v1/health")

    assert console.status_code == 200
    assert fallback.status_code == 200
    assert "Local Mery admin console" in console.text
    assert fallback.text == console.text
    assert script.status_code == 200
    assert "fetch(`/v1${path}`" in script.text
    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".shell" in styles.text
    assert missing_asset.status_code == 404
    assert traversal_asset.status_code == 404
    assert v1_missing.status_code == 401


def test_model_install_requires_explicit_user_confirmation() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    headers = {"Authorization": "Bearer " + "secret" * 8}

    with TestClient(app) as client:
        blocked = client.post(
            "/v1/models/install",
            headers=headers,
            json={"schema_version": "v1", "request_id": "test", "model_id": "pack.en-us"},
        )
        confirmed = client.post(
            "/v1/models/install",
            headers=headers,
            json={
                "schema_version": "v1",
                "request_id": "test",
                "model_id": "pack.en-us",
                "user_confirmed": True,
            },
        )

    assert blocked.status_code == 409
    assert blocked.json()["code"] == "update.confirmation_required"
    assert blocked.json()["recommended_action"] == "confirm_update"
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] in {"queued", "running"}


def test_console_assets_require_confirmation_before_install_request() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        script = client.get("/console/assets/app.js").text

    confirm_index = script.index("window.confirm")
    install_post_index = script.index('apiJson("/models/install"')
    assert confirm_index < install_post_index
    assert "Source:" in script
    assert "Size:" in script
    assert "License:" in script
    assert "Version:" in script
    assert "Capability impact:" in script
    assert "user_confirmed: true" in script


def test_storage_endpoint_exposes_breakdown_and_advisory_threshold(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_STORAGE_WARN_BYTES", "6")
    (tmp_path / "models" / "kokoro" / "voice-a").mkdir(parents=True)
    (tmp_path / "models" / "kokoro" / "voice-a" / "model.bin").write_bytes(b"1234")
    (tmp_path / "cache" / "downloads").mkdir(parents=True)
    (tmp_path / "cache" / "downloads" / "artifact.tmp").write_bytes(b"12")
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "logs" / "mery.log").write_bytes(b"123")
    (tmp_path / "diagnostics").mkdir(parents=True)
    (tmp_path / "diagnostics" / "last-doctor.json").write_bytes(b"12345")
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get(
            "/v1/storage",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["breakdown"] == {
        "models": 4,
        "cache": 2,
        "logs": 3,
        "diagnostics": 5,
    }
    assert body["advisory"] == {
        "threshold_bytes": 6,
        "used_bytes": 14,
        "status": "warn",
        "message": "storage usage exceeds advisory threshold; cleanup is user-controlled",
    }


def test_console_assets_render_storage_advisory_as_informational() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        html = client.get("/console").text
        script = client.get("/console/assets/app.js").text

    assert 'id="storage-summary"' in html
    assert "Storage advisory" in html
    assert 'apiJson("/storage")' in script
    assert "renderStorageSummary" in script
    assert "cleanup is user-controlled" in script
    assert 'data-cleanup-target="cache"' in html
    assert "auto-delete" not in html.lower()
    assert "auto-delete" not in script.lower()


def test_storage_cleanup_endpoint_clears_safe_targets_and_protects_models(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    (tmp_path / "models" / "kokoro" / "active-voice").mkdir(parents=True)
    model_path = tmp_path / "models" / "kokoro" / "active-voice" / "model.bin"
    model_path.write_bytes(b"model")
    (tmp_path / "cache" / "downloads").mkdir(parents=True)
    (tmp_path / "cache" / "downloads" / "artifact.tmp").write_bytes(b"cache")
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    headers = {"Authorization": "Bearer " + "secret" * 8}

    with TestClient(app) as client:
        cleaned = client.post(
            "/v1/storage/cleanup",
            headers=headers,
            json={"schema_version": "v1", "request_id": "test", "target": "cache"},
        )
        refused = client.post(
            "/v1/storage/cleanup",
            headers=headers,
            json={"schema_version": "v1", "request_id": "test", "target": "models"},
        )

    assert cleaned.status_code == 200
    assert cleaned.json()["target"] == "cache"
    assert cleaned.json()["models_protected"] is True
    assert cleaned.json()["removed_entries"] == 1
    assert refused.status_code == 409
    assert refused.json()["code"] == "storage.model_cleanup_refused"
    assert model_path.read_bytes() == b"model"
    assert not (tmp_path / "cache" / "downloads" / "artifact.tmp").exists()


def test_console_assets_expose_safe_storage_cleanup_actions() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        html = client.get("/console").text
        script = client.get("/console/assets/app.js").text

    assert 'data-cleanup-target="cache"' in html
    assert 'data-cleanup-target="logs"' in html
    assert 'data-cleanup-target="diagnostics"' in html
    assert 'data-cleanup-target="models"' not in html
    assert 'apiJson("/storage/cleanup"' in script
    assert "models_protected" in script
    assert "cleanup is user-controlled" in script


def test_console_assets_pin_token_catalog_speech_and_diagnostics_behaviour() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        html = client.get("/console").text
        script = client.get("/console/assets/app.js").text

    assert "Remember on this device" in html
    assert "Token storage: memory only" in html
    assert 'id="locale-filter"' in html
    assert "Selected voice locale: none" in html
    assert "response_format=wav and stream=false" in html
    assert "localStorage.setItem(TOKEN_STORAGE_KEY" in script
    assert "localStorage.removeItem(TOKEN_STORAGE_KEY" in script
    assert 'apiJson("/catalog/voices")' in script
    assert 'apiJson("/voices/installed")' in script
    assert 'const localeFilter = document.querySelector("#locale-filter")' in script
    assert 'supported_locales' in script
    assert 'governanceStatus(voice)' in script
    assert 'governanceDetails(voice)' in script
    assert 'gated (${riskClass})' in script
    assert 'provenance unavailable' in script
    assert 'no consent required' in script
    assert 'data-upload' not in script
    assert 'data-clone' not in script
    assert 'data-reference' not in script
    assert 'reference-audio' not in script
    assert 'Selected voice locale:' in script
    assert "apiJson(`/models/install/${encodeURIComponent(jobId)}`)" in script
    assert "window.confirm" in script
    assert "user_confirmed: true" in script
    assert 'response_format: "wav"' in script
    assert "stream: false" in script
    assert "locale: voiceSelect" not in script
    assert "locale: localeFilter" not in script
    assert "URL.revokeObjectURL(activeObjectUrl)" in script
    assert 'apiJson("/diagnostics")' in script
    assert 'apiJson("/storage")' in script
    assert 'id="export-diagnostics"' in html
    assert "Download sanitized export" in html
    assert 'apiJson("/diagnostics/export")' in script
    assert "new Blob" in script
    assert "mery-diagnostics-" in script
    assert "User Mode backend summary" in html
    assert 'id="backend-summary"' in html
    assert "Developer Mode backend selection" in html
    assert 'id="toggle-developer-mode"' in html
    assert 'id="backend-developer-controls" class="developer-only" hidden' in html
    assert "toggleDeveloperMode" in script
    assert "renderBackendSummary" in script
    assert "backend_selection" in script
    assert "selected_backend" in script
    assert "missing_extras" in script
    assert "Override controls are hidden from normal first-run users" in html


def test_diagnostics_expose_governance_blocks_as_user_actionable_checks() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get(
            "/v1/diagnostics",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )

    assert response.status_code == 200
    checks = response.json()["checks"]
    assert checks["governance.gated_features"] == "user_action_required:synthesis.gated_feature"
    assert checks["governance.community_catalogs"] == (
        "user_action_required:catalog.community_disabled"
    )


def test_diagnostics_history_status_and_delete_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    DiagnosticsEventStore(data_dir=tmp_path).append(
        DiagnosticsEvent(
            event_id="evt-history-api",
            event_type="readiness.changed",
            occurred_at=datetime.now(UTC),
            severity="info",
            source="api-test",
            message="readiness changed",
            metadata={"ready": True, "raw_text": "private"},
        )
    )
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        history = client.get(
            "/v1/diagnostics/history",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )
        deleted = client.delete(
            "/v1/diagnostics/history",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )
        after = client.get(
            "/v1/diagnostics/history",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )

    assert history.status_code == 200
    body = history.json()
    assert body["retention_status"]["event_count"] == 1
    assert body["retention_status"]["retention_days"] == 7
    assert body["retention_status"]["max_events"] == 1000
    assert body["events"][0]["event_id"] == "evt-history-api"
    assert body["events"][0]["metadata"] == {"ready": True}
    assert deleted.status_code == 200
    assert deleted.json() == {"schema_version": "v1", "request_id": "local", "deleted_events": 1}
    assert after.json()["retention_status"]["event_count"] == 0
    assert after.json()["events"] == []


def test_diagnostics_export_endpoint_returns_sanitized_bundle(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    DiagnosticsEventStore(data_dir=tmp_path).append(
        DiagnosticsEvent(
            event_id="evt-export-api",
            event_type="error.sanitized",
            occurred_at=datetime.now(UTC),
            severity="error",
            source="api-test",
            message="sanitized error captured",
            metadata={
                "voice_id": "voice.en.demo",
                "raw_text": "private user text",
                "token": "Bearer private",
                "audio_b64": "UklGRg==",
                "path": "/Users/private/model.onnx",
            },
        )
    )
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get(
            "/v1/diagnostics/export",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )

    assert response.status_code == 200
    bundle = response.json()
    assert bundle["schema_version"] == "v1"
    assert bundle["bundle_type"] == "diagnostics_export"
    assert bundle["recent_diagnostics"][0]["metadata"] == {"voice_id": "voice.en.demo"}
    serialized = response.text
    assert "private user text" not in serialized
    assert "Bearer private" not in serialized
    assert "UklGRg" not in serialized
    assert "/Users/private" not in serialized


def test_diagnostics_expose_persisted_sanitized_event_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    DiagnosticsEventStore(data_dir=tmp_path).append(
        DiagnosticsEvent(
            event_id="evt-api-1",
            event_type="synthesis.metadata",
            occurred_at=datetime.now(UTC),
            severity="info",
            source="api-test",
            message="synthesis metadata captured",
            metadata={
                "voice_id": "voice.en.demo",
                "duration_ms": 42,
                "raw_text": "secret user text",
                "token": "Bearer private",
                "path": "/Users/private/model.onnx",
                "audio_b64": "UklGRg==",
            },
        )
    )
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get(
            "/v1/diagnostics",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )

    assert response.status_code == 200
    events = response.json()["events"]
    assert events == [
        {
            "schema_version": "v1",
            "event_id": "evt-api-1",
            "event_type": "synthesis.metadata",
            "occurred_at": events[0]["occurred_at"],
            "severity": "info",
            "source": "api-test",
            "message": "synthesis metadata captured",
            "metadata": {"duration_ms": 42, "voice_id": "voice.en.demo"},
        }
    ]


def test_catalog_voices_expose_bundled_curated_trust_tier() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get(
            "/v1/catalog/voices",
            headers={"Authorization": "Bearer " + "secret" * 8},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["voices"]
    assert {voice["trust_tier"] for voice in body["voices"]} == {"bundled_curated"}


def test_rest_endpoint_requires_bearer_token() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        missing = client.get("/v1/health")
        invalid = client.get("/v1/health", headers={"Authorization": "Bearer wrong"})

    assert missing.status_code == 401
    assert missing.json()["code"] == "auth.token_missing"
    assert missing.json()["recommended_action"] == "pair_client"
    assert missing.json()["fallback_policy"] == "none"
    assert missing.json()["request_id"] == "local"
    assert missing.json()["sanitized_diagnostic"] == "reason=authorization missing"
    assert invalid.status_code == 401
    assert invalid.json()["code"] == "auth.token_invalid"
    assert invalid.json()["recommended_action"] == "pair_client"
    assert invalid.json()["fallback_policy"] == "none"
    assert invalid.json()["request_id"] == "local"
    assert invalid.json()["sanitized_diagnostic"] == "reason=authorization invalid"


def test_running_app_reloads_rotated_auth_token(tmp_path) -> None:
    config_store = HelperConfigStore(tmp_path / "config")
    original = config_store.load_or_create()
    app = create_app(config_store=config_store)

    rotated = config_store.rotate_token()

    with TestClient(app) as client:
        old_token = client.get(
            "/v1/health",
            headers={"Authorization": f"Bearer {original.auth_token}"},
        )
        new_token = client.get(
            "/v1/health",
            headers={"Authorization": f"Bearer {rotated.auth_token}"},
        )

    assert old_token.status_code == 401
    assert old_token.json()["code"] == "auth.token_invalid"
    assert old_token.json()["recommended_action"] == "pair_client"
    assert new_token.status_code == 200


def test_cli_rotate_invalidates_old_token_and_allows_fresh_repair(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    config_store = HelperConfigStore(tmp_path / "config")
    original = config_store.load_or_create()
    app = create_app(config_store=config_store)

    rotate_result = CliRunner().invoke(cli_app, ["pair", "--rotate"])
    rotated = config_store.load_or_create()
    pair_result = CliRunner().invoke(cli_app, ["pair"])
    code_line = next(
        line for line in pair_result.stdout.splitlines() if line.startswith("Pairing code:")
    )
    code = code_line.removeprefix("Pairing code:").strip()

    with TestClient(app) as client:
        old_token = client.get(
            "/v1/health",
            headers={"Authorization": f"Bearer {original.auth_token}"},
        )
        new_token = client.get(
            "/v1/health",
            headers={"Authorization": f"Bearer {rotated.auth_token}"},
        )
        repaired = client.post("/v1/pair/claim", json={"pairing_code": code})

    assert rotate_result.exit_code == 0
    assert pair_result.exit_code == 0
    assert rotated.helper_id == original.helper_id
    assert rotated.auth_token != original.auth_token
    assert old_token.status_code == 401
    assert new_token.status_code == 200
    assert repaired.status_code == 200
    assert repaired.json()["helper_id"] == original.helper_id
    assert repaired.json()["auth_token"] == rotated.auth_token


def test_origin_allowlist_rejects_prefix_bypass() -> None:
    assert is_allowed_origin("http://localhost") is True
    assert is_allowed_origin("http://127.0.0.1:8765") is True
    assert is_allowed_origin("null") is True
    assert is_allowed_origin("http://localhost.evil") is False
    assert is_allowed_origin("https://localhost") is False


def test_unknown_origin_and_oversized_request_are_rejected() -> None:
    app = create_app(
        config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765),
        max_body_bytes=4,
    )

    with TestClient(app) as client:
        origin = client.get(
            "/v1/health",
            headers={"Authorization": "Bearer " + "secret" * 8, "Origin": "https://evil.example"},
        )
        prefix_bypass = client.get(
            "/v1/health",
            headers={"Authorization": "Bearer " + "secret" * 8, "Origin": "http://localhost.evil"},
        )
        oversized = client.post(
            "/v1/diagnostics",
            headers={"Authorization": "Bearer " + "secret" * 8},
            content=b"12345",
        )
        malformed_length = client.post(
            "/v1/diagnostics",
            headers={
                "Authorization": "Bearer " + "secret" * 8,
                "Content-Length": "not-a-number",
            },
            content=b"1",
        )

    assert origin.status_code == 403
    assert origin.json()["code"] == "security.unsafe_identifier"
    assert origin.json()["request_id"] == "local"
    assert prefix_bypass.status_code == 403
    assert prefix_bypass.json()["code"] == "security.unsafe_identifier"
    assert prefix_bypass.json()["request_id"] == "local"
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "security.request_too_large"
    assert oversized.json()["request_id"] == "local"
    assert malformed_length.status_code == 400
    assert malformed_length.json()["code"] == "security.request_too_large"
    assert malformed_length.json()["request_id"] == "local"


def test_websocket_events_requires_bearer_token() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with (
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/v1/events"),
    ):
        pass


def test_websocket_events_rejects_invalid_bearer_token() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with (
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(
            "/v1/events",
            headers={"Authorization": "Bearer wrong", "Origin": "null"},
        ),
    ):
        pass

    assert exc_info.value.code == 1008


def test_websocket_events_rejects_unknown_origin() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with (
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(
            "/v1/events",
            headers={
                "Authorization": "Bearer " + "secret" * 8,
                "Origin": "https://evil.example",
            },
        ),
    ):
        pass

    assert exc_info.value.code == 1008


def test_websocket_events_accepts_valid_handshake() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with (
        TestClient(app) as client,
        client.websocket_connect(
            "/v1/events",
            headers={"Authorization": "Bearer " + "secret" * 8, "Origin": "null"},
        ) as websocket,
    ):
        assert websocket.receive_json() == {
            "schema_version": "v1",
            "request_id": "local",
            "event_type": "helper.statusChanged",
            "status": "ok",
        }


def test_websocket_events_accepts_mery_events_subprotocol() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with (
        TestClient(app) as client,
        client.websocket_connect(
            "/v1/events",
            headers={
                "Authorization": "Bearer " + "secret" * 8,
                "Origin": "null",
                "Sec-WebSocket-Protocol": "mery.events.v1",
            },
            subprotocols=["mery.events.v1"],
        ) as websocket,
    ):
        assert websocket.receive_json() == {
            "schema_version": "v1",
            "request_id": "local",
            "event_type": "helper.statusChanged",
            "status": "ok",
        }
