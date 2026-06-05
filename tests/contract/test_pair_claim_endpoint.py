from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService


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
