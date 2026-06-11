from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.security.config import HelperConfig


def _auth() -> dict[str, str]:
    return {"Authorization": "Bearer " + "secret" * 8}


def test_prometheus_metrics_disabled_by_default() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))

    with TestClient(app) as client:
        response = client.get("/metrics", headers=_auth())

    assert response.status_code == 404


def test_prometheus_metrics_enabled_only_by_explicit_opt_in() -> None:
    app = create_app(
        config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765),
        enable_metrics=True,
    )

    with TestClient(app) as client:
        response = client.get("/metrics", headers=_auth())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "# HELP mery_info" in body
    assert "# TYPE mery_info gauge" in body
    assert 'mery_info{contract_version="v1"} 1' in body
    assert "mery_usable_voices" in body
    assert "mery_installed_voices" in body
    assert "http://" not in body
    assert "https://" not in body


def test_metrics_source_contains_no_outbound_telemetry_clients() -> None:
    source = "\n".join(
        [
            __import__("pathlib").Path("src/mery_tts/api/app.py").read_text(),
        ]
    )

    forbidden = ["requests.", "httpx.", "urllib.request", "socket.create_connection"]
    assert not any(marker in source for marker in forbidden)
