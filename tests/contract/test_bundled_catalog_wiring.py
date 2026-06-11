"""Integration tests for bundled catalog wiring into voice_pack_graph (ADR-0027, ADR-0030).

Verifies that the bundled catalog (shipped with the package) is wired into
the FastAPI app at startup, populating /v1/voice-packs and
/v1/setup/recommendations with real voice packs derived from the bundled
fixture models.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.security.config import HelperConfig

AUTH_TOKEN = "token" * 8
AUTH_HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def _make_client() -> TestClient:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token=AUTH_TOKEN, port=8765))
    return TestClient(app)


def test_voice_packs_returns_bundled_locale_packs() -> None:
    """Bundled catalog groups voices by locale; expect en-us and vi-vn packs."""
    with _make_client() as client:
        response = client.get("/v1/voice-packs", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    packs_by_id = {pack["voice_pack_id"]: pack for pack in body["voice_packs"]}
    assert "pack.en-us" in packs_by_id
    assert "pack.vi-vn" in packs_by_id
    assert packs_by_id["pack.en-us"]["supported_locales"] == ["en-US"]
    assert packs_by_id["pack.vi-vn"]["supported_locales"] == ["vi-VN"]


def test_voice_pack_has_populated_voice_ids() -> None:
    """Each pack should reference the voices from the bundled catalog."""
    with _make_client() as client:
        response = client.get("/v1/voice-packs", headers=AUTH_HEADERS)
    assert response.status_code == 200
    packs_by_id = {pack["voice_pack_id"]: pack for pack in response.json()["voice_packs"]}
    vi_pack = packs_by_id["pack.vi-vn"]
    assert any(v.startswith("catalog.piper-plus.vi-vn") for v in vi_pack["voice_ids"])
    en_pack = packs_by_id["pack.en-us"]
    assert any(v.startswith("catalog.kokoro.en-us") for v in en_pack["voice_ids"])


def test_setup_recommendations_ranks_locale_match_first() -> None:
    """locale=vi-vn should rank pack.vi-vn above pack.en-us."""
    with _make_client() as client:
        response = client.get(
            "/v1/setup/recommendations?client=generic&intent=general&locale=vi-vn",
            headers=AUTH_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    recs = body["recommendations"]
    assert len(recs) >= 2
    assert recs[0]["voice_pack_id"] == "pack.vi-vn"
    assert recs[0]["locale"] == "vi-VN"
    assert recs[0]["supported_locales"] == ["vi-VN"]


def test_setup_recommendations_ranks_en_us_for_english_locale() -> None:
    """locale=en-us should rank pack.en-us first."""
    with _make_client() as client:
        response = client.get(
            "/v1/setup/recommendations?client=generic&intent=general&locale=en-us",
            headers=AUTH_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    recs = body["recommendations"]
    assert len(recs) >= 2
    assert recs[0]["voice_pack_id"] == "pack.en-us"
    assert recs[0]["locale"] == "en-US"


def test_setup_recommendations_use_case_inference() -> None:
    """Inferred use_case should reflect voice recommended_uses, not test markers."""
    with _make_client() as client:
        response = client.get(
            "/v1/setup/recommendations?client=generic&intent=general",
            headers=AUTH_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    recs = body["recommendations"]
    use_cases = {r["use_case"] for r in recs}
    assert "offline-test" not in use_cases
    assert "test" not in use_cases
    assert "" not in use_cases
