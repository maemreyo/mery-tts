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
