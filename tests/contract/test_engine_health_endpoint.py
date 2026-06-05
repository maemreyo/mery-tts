from collections.abc import AsyncIterator

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
        return "unavailable: token secret traceback"

    async def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
        yield PCMChunk(pcm=text.encode(), sample_rate_hz=24_000, channels=1)


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
