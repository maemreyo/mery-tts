from fastapi.testclient import TestClient
from typer.testing import CliRunner

from mery_tts.api.app import create_app
from mery_tts.cli.main import app as cli_app
from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService


def test_pair_claim_endpoint_rate_limits_failed_claims(tmp_path):
    store = HelperConfigStore(tmp_path)
    config = store.load_or_create()
    pairing = PairingService(config_store=store, config=config, max_failed_claims=2)
    pairing.create_challenge()
    app = create_app(config=config, pairing_service=pairing)

    with TestClient(app) as client:
        first = client.post("/v1/pair/claim", json={"pairing_code": "WRONG1"})
        second = client.post("/v1/pair/claim", json={"pairing_code": "WRONG2"})
        throttled = client.post("/v1/pair/claim", json={"pairing_code": "WRONG3"})

    assert first.status_code == 401
    assert second.status_code == 401
    assert throttled.status_code == 429
    assert throttled.json()["code"] == "auth.rate_limited"
    assert "WRONG3" not in throttled.text


def test_cli_created_pairing_challenge_can_be_claimed_through_http_once(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    cli_result = CliRunner().invoke(cli_app, ["pair"])
    code_line = next(
        line for line in cli_result.stdout.splitlines() if line.startswith("Pairing code:")
    )
    code = code_line.removeprefix("Pairing code:").strip()
    store = HelperConfigStore(tmp_path / "config")
    config = store.load_or_create()
    app = create_app(
        config=config,
        pairing_service=PairingService(config_store=store, config=config),
    )

    with TestClient(app) as client:
        claimed = client.post("/v1/pair/claim", json={"pairing_code": code})
        reused = client.post("/v1/pair/claim", json={"pairing_code": code})

    assert cli_result.exit_code == 0
    assert claimed.status_code == 200
    assert claimed.json()["auth_token"] == config.auth_token
    assert reused.status_code == 401


def test_pair_claim_endpoint_exchanges_code_for_long_lived_token(tmp_path):
    store = HelperConfigStore(tmp_path)
    config = store.load_or_create()
    pairing = PairingService(config_store=store, config=config)
    challenge = pairing.create_challenge()
    app = create_app(config=config, pairing_service=pairing)

    with TestClient(app) as client:
        response = client.post("/v1/pair/claim", json={"pairing_code": challenge.code})
        reused = client.post("/v1/pair/claim", json={"pairing_code": challenge.code})

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "v1"
    assert body["helper_id"] == config.helper_id
    assert body["auth_token"] == config.auth_token
    assert body["contract_version"] == "v1"
    assert "rest" in body["capabilities"]
    assert reused.status_code == 401
