from pathlib import Path

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.storage.identity import StorageIdentityStore

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


def test_catalog_voices_returns_bundled_runtime_catalog(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    app = create_app(config=config, model_store=ModelStore(tmp_path))

    with TestClient(app) as client:
        response = client.get("/v1/catalog/voices", headers=HEADERS)

    assert response.status_code == 200
    voices = response.json()["voices"]
    assert {voice["voice_id"] for voice in voices} == {
        "catalog.piper-plus.vi-vn.demo",
        "catalog.kokoro.en-us.af-heart.demo",
    }
    assert {voice["engine_id"] for voice in voices} == {"piper-plus", "kokoro"}


def test_installed_voices_returns_persisted_voice_manifests(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    identity_store = StorageIdentityStore(tmp_path)
    identity_store.write_artifact_manifest(
        engine_id="kokoro",
        artifact_id="artifact.kokoro",
        metadata={"catalogEntryId": "entry.kokoro"},
    )
    identity_store.write_voice_manifest(
        "voice.kokoro.af",
        ["artifact.kokoro"],
        {"kind": "preset", "preset_id": "af_heart"},
    )
    app = create_app(config=config, model_store=ModelStore(tmp_path))

    with TestClient(app) as client:
        response = client.get("/v1/voices/installed", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["voices"] == [
        {
            "voice_id": "voice.kokoro.af",
            "engine_id": "kokoro",
            "display_name": "Voice Kokoro Af",
        }
    ]


def test_model_delete_is_idempotent_for_missing_model(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    app = create_app(config=config, model_store=ModelStore(tmp_path))

    with TestClient(app) as client:
        response = client.delete("/v1/models/missing", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["deleted"] is False


def test_model_routes_reject_unsafe_model_ids(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    app = create_app(config=config, model_store=ModelStore(tmp_path))

    unsafe_paths = [
        "/v1/models/..%2Fsecret",
        "/v1/models/..%5Csecret",
        "/v1/models/%2FUsers%2Fprivate%2Fmodel",
        "/v1/models/C:%5CUsers%5Cprivate%5Cmodel",
    ]

    with TestClient(app) as client:
        responses = [
            response
            for path in unsafe_paths
            for response in (
                client.get(path, headers=HEADERS),
                client.delete(path, headers=HEADERS),
            )
        ]

    assert {response.status_code for response in responses} == {400}
    assert {response.json()["code"] for response in responses} == {"security.unsafe_identifier"}


def test_model_install_accepts_stable_model_id_only(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    app = create_app(config=config, model_store=ModelStore(tmp_path))

    with TestClient(app) as client:
        response = client.post(
            "/v1/models/install",
            headers=HEADERS,
            json={"schema_version": "v1", "request_id": "local", "model_id": "piper.demo"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "v1"
    assert payload["request_id"] == "local"
    assert payload["job_id"].startswith("job-")
    assert payload["status"] == "running"


def test_model_install_rejects_paths_and_urls_before_domain_work(tmp_path: Path) -> None:
    config = (
        HelperConfigStore(tmp_path / "config")
        .load_or_create()
        .model_copy(update={"auth_token": TOKEN})
    )
    app = create_app(config=config, model_store=ModelStore(tmp_path))
    unsafe_ids = [
        "../secret",
        "/Users/private/model.onnx",
        "C:\\Users\\private\\model.onnx",
        "https://example.com/model.onnx",
        "file:///tmp/model.onnx",
    ]

    with TestClient(app) as client:
        responses = [
            client.post(
                "/v1/models/install",
                headers=HEADERS,
                json={"schema_version": "v1", "request_id": "local", "model_id": model_id},
            )
            for model_id in unsafe_ids
        ]

    assert {response.status_code for response in responses} == {400}
    assert {response.json()["code"] for response in responses} == {"security.unsafe_identifier"}
    assert not any(tmp_path.iterdir()) or {path.name for path in tmp_path.iterdir()} == {"config"}


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
