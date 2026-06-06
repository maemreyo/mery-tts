from collections.abc import AsyncIterator
from dataclasses import dataclass

from fastapi.testclient import TestClient

from mery_tts.api.app import create_app
from mery_tts.engines.base import EngineAdapter, EngineRegistry, PCMChunk
from mery_tts.security.config import HelperConfig
from mery_tts.voice import VoiceDescriptor

TOKEN = "secret" * 8


class DegradedAdapter(EngineAdapter):
    engine_id = "degraded"
    accepted_voice_kinds = frozenset({"preset"})

    def health(self) -> str:
        return "degraded: missing optional voice cache at /Users/private/path"

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


class UnavailableAdapter(EngineAdapter):
    engine_id = "unavailable"
    accepted_voice_kinds = frozenset({"preset"})

    def health(self) -> str:
        return "unavailable: token secret Traceback from kokoro_onnx"

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


class DependencyMissingAdapter(EngineAdapter):
    engine_id = "dependency-missing"
    accepted_voice_kinds = frozenset({"preset"})

    def health(self) -> str:
        return "dependency_missing: ModuleNotFoundError: No module named 'piper_plus'"

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


class ModelMissingAdapter(EngineAdapter):
    engine_id = "model-missing"
    accepted_voice_kinds = frozenset({"preset"})

    def health(self) -> str:
        return "model_missing: missing model at /Users/me/models/voice.onnx"

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


class RuntimeUnavailableAdapter(EngineAdapter):
    engine_id = "runtime-unavailable"
    accepted_voice_kinds = frozenset({"preset"})

    def health(self) -> str:
        return (
            "runtime_unavailable: RuntimeError: dlopen(/Users/me/lib.dylib) failed; api_key=secret"
        )

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


class DiscoveredAdapter(EngineAdapter):
    engine_id = "discovered"
    accepted_voice_kinds = frozenset({"preset"})

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


@dataclass(frozen=True)
class FakeEntryPoint:
    name: str
    adapter_class: type[EngineAdapter] | None

    def load(self) -> type[EngineAdapter]:
        if self.adapter_class is None:
            raise ImportError("optional dependency missing")
        return self.adapter_class


@dataclass(frozen=True)
class FakeEntryPoints:
    entries: tuple[FakeEntryPoint, ...]

    def select(self, *, group: str) -> tuple[FakeEntryPoint, ...]:
        assert group == "mery_tts.engines"
        return self.entries


def test_engines_endpoint_exposes_safe_runtime_health() -> None:
    registry = EngineRegistry(
        adapters={"degraded": DegradedAdapter(), "unavailable": UnavailableAdapter()},
        load_warnings=("broken: optional dependency missing",),
    )
    app = create_app(
        config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765),
        engine_registry=registry,
    )

    with TestClient(app) as client:
        response = client.get("/v1/engines", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    engines = {item["engine_id"]: item for item in response.json()["engines"]}
    assert engines["degraded"]["status"] == "degraded"
    assert engines["unavailable"]["status"] == "unavailable"
    assert "/Users" not in engines["degraded"]["reason"]
    assert "secret" not in engines["unavailable"]["reason"]
    assert "Traceback" not in engines["unavailable"]["reason"]
    assert "kokoro_onnx" not in engines["unavailable"]["reason"]


def test_engines_endpoint_differentiates_runtime_health_failure_reasons() -> None:
    registry = EngineRegistry(
        adapters={
            "dependency-missing": DependencyMissingAdapter(),
            "model-missing": ModelMissingAdapter(),
            "runtime-unavailable": RuntimeUnavailableAdapter(),
            "discovered": DiscoveredAdapter(),
        },
    )
    app = create_app(
        config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765),
        engine_registry=registry,
    )

    with TestClient(app) as client:
        response = client.get("/v1/engines", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    engines = {item["engine_id"]: item for item in response.json()["engines"]}
    assert engines["discovered"] == {
        "engine_id": "discovered",
        "status": "available",
        "reason": None,
    }
    assert engines["dependency-missing"] == {
        "engine_id": "dependency-missing",
        "status": "unavailable",
        "reason": "dependency_missing: ModuleNotFoundError: No module named '[redacted-package]'",
    }
    assert engines["model-missing"] == {
        "engine_id": "model-missing",
        "status": "degraded",
        "reason": "model_missing: missing model at [redacted-path]/me/models/voice.onnx",
    }
    assert engines["runtime-unavailable"] == {
        "engine_id": "runtime-unavailable",
        "status": "unavailable",
        "reason": (
            "runtime_unavailable: RuntimeError: dlopen([redacted-path]/me/lib.dylib) "
            "failed; api_key=[redacted]"
        ),
    }


def test_app_factory_discovers_engine_entry_points_by_default(monkeypatch) -> None:
    monkeypatch.setattr(
        "mery_tts.engines.discovery.entry_points",
        lambda: FakeEntryPoints(
            (
                FakeEntryPoint(name="discovered", adapter_class=DiscoveredAdapter),
                FakeEntryPoint(name="missing", adapter_class=None),
            )
        ),
    )
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token=TOKEN, port=8765))

    with TestClient(app) as client:
        response = client.get("/v1/engines", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    engines = {item["engine_id"]: item for item in response.json()["engines"]}
    assert set(engines) == {"discovered"}
    assert engines["discovered"]["status"] == "available"
