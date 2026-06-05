from mery_tts.schemas.v1 import (
    AudioEvent,
    CatalogVoicesResponse,
    HealthResponse,
    InstallEvent,
    PairingResponse,
    SynthesisEvent,
)


def test_rest_schema_contracts_include_version_and_correlation_fields() -> None:
    health = HealthResponse(request_id="req-1", status="ok")
    catalog = CatalogVoicesResponse(request_id="req-2", voices=[])
    pairing = PairingResponse(
        request_id="req-3", pairing_code="123456", setup_url="http://127.0.0.1:8765/pair/123456"
    )

    assert health.schema_version == "v1"
    assert catalog.schema_version == "v1"
    assert pairing.schema_version == "v1"
    assert health.request_id == "req-1"


def test_event_schema_contracts_cover_install_synthesis_audio() -> None:
    install = InstallEvent(event_type="install.completed", request_id="req", job_id="job")
    synthesis = SynthesisEvent(event_type="synthesize.started", request_id="req", session_id="sess")
    audio = AudioEvent(event_type="audio.chunk", request_id="req", session_id="sess", chunk_index=0)

    assert install.schema_version == "v1"
    assert synthesis.schema_version == "v1"
    assert audio.schema_version == "v1"
