import mery_tts


def test_package_imports_without_client_or_engine_dependencies() -> None:
    assert mery_tts.__version__ == "0.1.0"
    assert mery_tts.PUBLIC_API_BOUNDARY == "/v1"


def test_package_public_surface_is_minimal() -> None:
    assert set(mery_tts.__all__) == {"PUBLIC_API_BOUNDARY", "__version__"}
