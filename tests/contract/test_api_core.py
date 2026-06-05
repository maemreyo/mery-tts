from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.security.config import HelperConfig


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
    assert invalid.status_code == 401


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
        oversized = client.post(
            "/v1/diagnostics",
            headers={"Authorization": "Bearer " + "secret" * 8},
            content=b"12345",
        )

    assert origin.status_code == 403
    assert oversized.status_code == 413
