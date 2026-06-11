from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.engines.base import EngineAdapter, EngineRegistry, PCMChunk
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfig
from mery_tts.smoke.record import SmokeRecord, SmokeRecordStore, SmokeStatus
from mery_tts.storage.identity import StorageIdentityStore
from mery_tts.voice import VoiceDescriptor

TOKEN = "secret" * 8


class HealthyAdapter(EngineAdapter):
    engine_id = "healthy"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        yield PCMChunk(pcm=b"pcm", sample_rate_hz=24_000, channels=1)


class MissingDependencyAdapter(HealthyAdapter):
    engine_id = "missing"

    def health(self) -> str:
        return "dependency_missing: missing optional runtime"


def _app_with_adapters(
    tmp_path: Path,
    *,
    adapters: dict[str, EngineAdapter],
    installed_voice_engine_id: str | None = None,
    smoke_passed: bool = False,
):
    store = StorageIdentityStore(tmp_path)
    smoke_store = SmokeRecordStore(data_dir=tmp_path)
    if installed_voice_engine_id is not None:
        store.write_artifact_manifest(
            engine_id=installed_voice_engine_id,
            artifact_id="artifact.voice",
            metadata={"catalogEntryId": "voice.ready"},
        )
        store.write_voice_manifest(
            "voice.ready",
            ["artifact.voice"],
            {"kind": "preset", "preset_id": "ready"},
        )
        if smoke_passed:
            smoke_store.save(
                SmokeRecord(
                    voice_id="voice.ready",
                    engine_id=installed_voice_engine_id,
                    status=SmokeStatus.PASSED,
                    checked_at=datetime.now(UTC),
                )
            )
    return create_app(
        config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765),
        engine_registry=EngineRegistry(adapters=adapters),
        model_store=ModelStore(tmp_path),
        storage_identity_store=store,
        smoke_record_store=smoke_store,
    )


def test_health_live_but_not_ready_without_usable_voice(tmp_path: Path) -> None:
    app = _app_with_adapters(tmp_path, adapters={})

    with TestClient(app) as client:
        response = client.get("/v1/health", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    body = response.json()
    assert body["live"] == "alive"
    assert body["ready"] is False
    assert body["health_status"] == "unavailable"
    assert body["status"] == "unavailable"
    assert body["health_checks"]["process"] == "alive"
    assert body["health_checks"]["readiness"] == "not_ready"


def test_health_ready_when_at_least_one_usable_voice_can_synthesize(tmp_path: Path) -> None:
    app = _app_with_adapters(
        tmp_path,
        adapters={"healthy": HealthyAdapter()},
        installed_voice_engine_id="healthy",
        smoke_passed=True,
    )

    with TestClient(app) as client:
        response = client.get("/v1/health", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    body = response.json()
    assert body["live"] == "alive"
    assert body["ready"] is True
    assert body["health_status"] == "ok"
    assert body["status"] == "ready"
    assert body["total_usable_voices"] == 1
    assert body["health_checks"]["readiness"] == "ready"


def test_health_degraded_when_ready_but_subsystem_unavailable(tmp_path: Path) -> None:
    app = _app_with_adapters(
        tmp_path,
        adapters={"healthy": HealthyAdapter(), "missing": MissingDependencyAdapter()},
        installed_voice_engine_id="healthy",
    )

    with TestClient(app) as client:
        response = client.get("/v1/health", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    body = response.json()
    assert body["live"] == "alive"
    assert body["ready"] is True
    assert body["health_status"] == "degraded"
    assert body["status"] == "degraded"
    assert body["health_checks"]["engine:missing"] == "unavailable"


def test_health_unavailable_when_engines_exist_but_no_voice_is_usable(tmp_path: Path) -> None:
    app = _app_with_adapters(tmp_path, adapters={"healthy": HealthyAdapter()})

    with TestClient(app) as client:
        response = client.get("/v1/health", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    body = response.json()
    assert body["live"] == "alive"
    assert body["ready"] is False
    assert body["health_status"] == "unavailable"
    assert body["status"] == "unavailable"
    assert body["health_checks"]["engine:healthy"] == "unavailable"
