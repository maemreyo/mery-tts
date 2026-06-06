import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from typer.testing import CliRunner

from mery_tts.api.app import create_app, is_allowed_origin
from mery_tts.cli.main import app as cli_app
from mery_tts.security.config import HelperConfig, HelperConfigStore


def test_app_factory_builds_without_engines_or_models() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="token" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get("/v1/health", headers={"Authorization": "Bearer " + "token" * 8})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["schema_version"] == "v1"


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
