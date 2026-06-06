from importlib import resources
from pathlib import Path

import mery_tts


def test_package_imports_without_client_or_engine_dependencies() -> None:
    assert mery_tts.__version__ == "0.1.0"
    assert mery_tts.PUBLIC_API_BOUNDARY == "/v1"


def test_package_public_surface_is_minimal() -> None:
    assert set(mery_tts.__all__) == {"PUBLIC_API_BOUNDARY", "__version__"}


def _files_importing(root: Path, module_name: str) -> list[Path]:
    return [path for path in root.rglob("*.py") if module_name in path.read_text()]


def test_audio_exporter_is_not_imported_by_api_modules() -> None:
    assert _files_importing(Path("src/mery_tts/api"), "mery_tts.audio.exporter") == []


def test_audio_player_is_not_imported_by_api_websocket_modules() -> None:
    assert _files_importing(Path("src/mery_tts/api/ws"), "mery_tts.audio.player") == []


def test_audio_encoder_is_not_imported_by_cli_modules() -> None:
    assert _files_importing(Path("src/mery_tts/cli"), "mery_tts.audio.encoder") == []


def test_console_assets_are_packaged_python_resources() -> None:
    console_package = resources.files("mery_tts.console")

    assert console_package.joinpath("index.html").is_file()
    assert console_package.joinpath("assets", "app.js").is_file()
    assert console_package.joinpath("assets", "app.css").is_file()
    assert "/v1${path}" in console_package.joinpath("assets", "app.js").read_text()


def test_readme_status_describes_current_runtime_without_stale_claims() -> None:
    readme = Path("README.md").read_text()

    assert "Early runtime implementation" in readme
    assert "packaged `/console` web UI" in readme
    assert "serves `/v1` plus the local web console at `/console`" in readme
    assert "No runtime implementation yet" not in readme
    assert "OpenAI-compatible speech stubs" not in readme
    assert "durable install lifecycle, packaging smoke" not in readme
