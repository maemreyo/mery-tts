"""Contract tests for setup and voice pack API endpoints (ADR-0027, ADR-0029, ADR-0030)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.security.config import HelperConfig

AUTH_TOKEN = "token" * 8
AUTH_HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def _make_client() -> TestClient:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token=AUTH_TOKEN, port=8765))
    return TestClient(app)


def test_voice_packs_endpoint_returns_schema() -> None:
    with _make_client() as client:
        response = client.get("/v1/voice-packs", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "v1"
    assert "voice_packs" in body
    assert isinstance(body["voice_packs"], list)


def test_setup_recommendations_endpoint_returns_schema() -> None:
    with _make_client() as client:
        response = client.get(
            "/v1/setup/recommendations?client=zam-reader&intent=english-reading",
            headers=AUTH_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "v1"
    assert "recommendations" in body
    assert body["client"] == "zam-reader"
    assert body["intent"] == "english-reading"


def test_setup_recommendations_requires_auth() -> None:
    with _make_client() as client:
        response = client.get("/v1/setup/recommendations")
    assert response.status_code == 401


def test_provider_runtimes_endpoint_returns_schema() -> None:
    with _make_client() as client:
        response = client.get("/v1/provider-runtimes", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "v1"
    assert "provider_runtimes" in body
    assert isinstance(body["provider_runtimes"], list)


def test_voice_pack_install_not_found() -> None:
    with _make_client() as client:
        response = client.post(
            "/v1/voice-packs/nonexistent/install",
            headers=AUTH_HEADERS,
        )
    assert response.status_code == 404


def test_install_jobs_endpoint_not_found() -> None:
    with _make_client() as client:
        response = client.get("/v1/install-jobs/nonexistent", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_console_setup_valid_intent() -> None:
    with _make_client() as client:
        response = client.get(
            "/console/setup?client=zam-reader&intent=english-reading",
        )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Mery Voice Setup" in response.text
    assert "zam-reader" in response.text


def test_console_setup_missing_client() -> None:
    with _make_client() as client:
        response = client.get("/console/setup?intent=english-reading")
    assert response.status_code == 200
    assert "Setup Intent Error" in response.text


def test_console_setup_missing_intent() -> None:
    with _make_client() as client:
        response = client.get("/console/setup?client=zam-reader")
    assert response.status_code == 200
    assert "Setup Intent Error" in response.text


def test_console_setup_unsafe_client_rejected() -> None:
    with _make_client() as client:
        response = client.get("/console/setup?client=http://evil.com&intent=english-reading")
    assert response.status_code == 200
    assert "Setup Intent Error" in response.text


def test_console_setup_is_public_no_auth() -> None:
    with _make_client() as client:
        response = client.get("/console/setup?client=generic&intent=general")
    assert response.status_code == 200
    assert "Mery Voice Setup" in response.text
