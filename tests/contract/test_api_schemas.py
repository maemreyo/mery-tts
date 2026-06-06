from mery_tts.api.app import create_app
from mery_tts.schemas.v1 import (
    AudioEvent,
    CatalogVoicesResponse,
    DiagnosticsResponse,
    EnginesResponse,
    HealthResponse,
    HelperStatusChangedEvent,
    InstalledVoicesResponse,
    InstallEvent,
    ModelDeleteResponse,
    ModelInstallRequest,
    ModelInstallResponse,
    ModelStatusResponse,
    PairingResponse,
    StorageResponse,
    SynthesisEvent,
)
from mery_tts.security.config import HelperConfig


def test_rest_schema_contracts_include_version_and_correlation_fields() -> None:
    responses = [
        HealthResponse(request_id="req-health", status="ok"),
        EnginesResponse(request_id="req-engines", engines=[]),
        InstalledVoicesResponse(request_id="req-installed", voices=[]),
        CatalogVoicesResponse(request_id="req-catalog", voices=[]),
        ModelInstallResponse(request_id="req-install", job_id="job-1", status="queued"),
        ModelStatusResponse(request_id="req-model", model_id="model.demo", status="not_installed"),
        ModelDeleteResponse(request_id="req-delete", model_id="model.demo", deleted=False),
        StorageResponse(request_id="req-storage", used_bytes=0, free_bytes=None),
        DiagnosticsResponse(request_id="req-diagnostics", checks={"daemon": "ok"}),
        PairingResponse(
            request_id="req-pair",
            pairing_code="123456",
            setup_url="http://127.0.0.1:8765/pair/123456",
        ),
    ]
    install_request = ModelInstallRequest(
        request_id="req-install-request",
        model_id="piper-plus.demo",
    )

    for response in responses:
        assert response.schema_version == "v1"
        assert response.request_id.startswith("req-")
    assert install_request.schema_version == "v1"
    assert install_request.request_id == "req-install-request"


def test_generated_openapi_schema_exposes_version_and_correlation_fields() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    schema = app.openapi()
    components = schema["components"]["schemas"]

    for component_name in [
        "HealthResponse",
        "EnginesResponse",
        "InstalledVoicesResponse",
        "CatalogVoicesResponse",
        "ModelInstallResponse",
        "ModelStatusResponse",
        "ModelDeleteResponse",
        "StorageResponse",
        "DiagnosticsResponse",
        "PairingResponse",
    ]:
        properties = components[component_name]["properties"]
        required = set(components[component_name]["required"])
        assert properties["schema_version"]["const"] == "v1"
        assert "request_id" in required

    install_request_properties = components["ModelInstallRequest"]["properties"]
    install_request_required = set(components["ModelInstallRequest"]["required"])
    assert install_request_properties["schema_version"]["const"] == "v1"
    assert {"request_id", "model_id"}.issubset(install_request_required)

    health_response = schema["paths"]["/v1/health"]["get"]["responses"]["200"]
    assert health_response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }


def test_generated_openapi_schema_documents_native_error_envelope() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    schema = app.openapi()
    components = schema["components"]["schemas"]

    error_properties = components["NativeErrorResponse"]["properties"]
    error_required = set(components["NativeErrorResponse"]["required"])
    assert {
        "code",
        "category",
        "severity",
        "recoverability",
        "user_message_key",
        "recommended_action",
        "fallback_policy",
        "sanitized_diagnostic",
        "request_id",
        "timestamp",
    }.issubset(error_required)
    assert error_properties["request_id"]["type"] == "string"

    for status_code in ["401", "403", "413"]:
        health_error = schema["paths"]["/v1/health"]["get"]["responses"][status_code]
        assert health_error["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/NativeErrorResponse"
        }

    for status_code in ["401", "403", "413"]:
        install_error = schema["paths"]["/v1/models/install"]["post"]["responses"][status_code]
        assert install_error["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/NativeErrorResponse"
        }

    health_responses = schema["paths"]["/v1/health"]["get"]["responses"]
    assert "400" not in health_responses


def test_event_schema_contracts_cover_install_synthesis_audio_and_helper_status() -> None:
    events = [
        InstallEvent(event_type="install.completed", request_id="req-install", job_id="job"),
        SynthesisEvent(
            event_type="synthesize.started",
            request_id="req-synthesis",
            session_id="sess",
        ),
        AudioEvent(
            event_type="audio.chunk",
            request_id="req-audio",
            session_id="sess",
            chunk_index=0,
        ),
        HelperStatusChangedEvent(
            event_type="helper.statusChanged",
            request_id="req-helper",
            status="ok",
        ),
    ]

    for event in events:
        assert event.schema_version == "v1"
        assert event.request_id.startswith("req-")


def test_generated_openapi_schema_includes_all_rest_endpoints() -> None:
    """Snapshot: verify OpenAPI schema documents all /v1 REST endpoints."""
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    schema = app.openapi()
    paths = schema["paths"]

    expected_paths = [
        "/v1/health",
        "/v1/engines",
        "/v1/voices/installed",
        "/v1/catalog/voices",
        "/v1/storage",
        "/v1/diagnostics",
        "/v1/models/install",
        "/v1/models/{model_id}",
        "/v1/pair/claim",
        "/v1/audio/speech",
    ]

    for path in expected_paths:
        assert path in paths, f"OpenAPI schema missing path: {path}"
