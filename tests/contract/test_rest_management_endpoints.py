from pathlib import Path

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService

TOKEN = "secret" * 8
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_management_endpoints_return_versioned_shapes(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    app = create_app(
        config=config,
        model_store=ModelStore(tmp_path),
    )

    with TestClient(app) as client:
        for path in [
            "/v1/health",
            "/v1/engines",
            "/v1/voices/installed",
            "/v1/catalog/voices",
            "/v1/storage",
            "/v1/diagnostics",
        ]:
            response = client.get(path, headers=HEADERS)
            assert response.status_code == 200
            assert response.json()["schema_version"] == "v1"


def test_model_status_delete_and_pair_claim_endpoints_exist(tmp_path: Path) -> None:
    model_dir = tmp_path / "kokoro" / "kokoro.en-us.demo"
    model_dir.mkdir(parents=True)
    (model_dir / "voice.bin").write_bytes(b"voice")
    store = HelperConfigStore(tmp_path / "config")
    config = store.load_or_create().model_copy(update={"auth_token": TOKEN})
    pairing = PairingService(config_store=store, config=config)
    challenge = pairing.create_challenge()
    app = create_app(
        config=config,
        model_store=ModelStore(tmp_path),
        pairing_service=pairing,
    )

    with TestClient(app) as client:
        status = client.get("/v1/models/kokoro.en-us.demo", headers=HEADERS)
        deleted = client.delete("/v1/models/kokoro.en-us.demo", headers=HEADERS)
        pair = client.post("/v1/pair/claim", json={"pairing_code": challenge.code})

    assert status.status_code == 200
    assert status.json()["status"] == "installed"
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert pair.status_code == 200
    assert pair.json()["schema_version"] == "v1"
