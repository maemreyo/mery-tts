import pytest
from pydantic import ValidationError

from mery_tts.contracts.bridge import InstallModelRequest, SynthesisRequest


def test_client_requests_accept_stable_ids_only() -> None:
    install = InstallModelRequest(contract_version="v1", model_id="piper-plus.en-us.lessac.medium")
    synthesis = SynthesisRequest(
        contract_version="v1",
        voice_id="kokoro.en.af_heart",
        text="Hello",
    )

    assert install.model_id == "piper-plus.en-us.lessac.medium"
    assert synthesis.voice_id == "kokoro.en.af_heart"


@pytest.mark.parametrize(
    "bad_id",
    ["../secret", "/tmp/model.onnx", "C:\\models\\voice.onnx", "https://example.com/model.onnx"],
)
def test_client_requests_reject_paths_and_urls(bad_id: str) -> None:
    with pytest.raises(ValidationError):
        InstallModelRequest(contract_version="v1", model_id=bad_id)


def test_public_response_schemas_do_not_expose_filesystem_paths() -> None:
    """Audit: public response schemas must not contain filesystem path or internal URL fields."""
    from mery_tts.schemas.v1 import (
        CatalogVoicesResponse,
        DiagnosticsResponse,
        EnginesResponse,
        HealthResponse,
        InstalledVoicesResponse,
        ModelDeleteResponse,
        ModelInstallResponse,
        ModelStatusResponse,
        NativeErrorResponse,
        StorageResponse,
    )

    responses_to_audit = [
        HealthResponse,
        EnginesResponse,
        InstalledVoicesResponse,
        CatalogVoicesResponse,
        ModelInstallResponse,
        ModelStatusResponse,
        ModelDeleteResponse,
        StorageResponse,
        DiagnosticsResponse,
        NativeErrorResponse,
    ]

    for response_cls in responses_to_audit:
        schema = response_cls.model_json_schema()
        properties = schema.get("properties", {})
        for prop_name in properties:
            assert "path" not in prop_name.lower(), (
                f"{response_cls.__name__} exposes suspicious field: {prop_name}"
            )
            assert "url" not in prop_name.lower(), (
                f"{response_cls.__name__} exposes suspicious field: {prop_name}"
            )
            assert "dir" not in prop_name.lower(), (
                f"{response_cls.__name__} exposes suspicious field: {prop_name}"
            )
