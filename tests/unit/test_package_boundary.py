import re
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
    index = console_package.joinpath("index.html")

    assert index.is_file()
    html = index.read_text()
    asset_paths = re.findall(r'"/console/assets/([^"]+\.(?:js|css))"', html)
    assert sorted(asset_paths) == sorted(set(asset_paths))
    assert any(path.endswith(".js") for path in asset_paths)
    assert any(path.endswith(".css") for path in asset_paths)
    for asset_path in asset_paths:
        assert console_package.joinpath("assets", asset_path).is_file()

    packaged_asset_names = {child.name for child in console_package.joinpath("assets").iterdir()}
    assert "app.js" not in packaged_asset_names
    assert "app.css" not in packaged_asset_names


def test_readme_status_describes_current_runtime_without_stale_claims() -> None:
    readme = Path("README.md").read_text()

    assert "Phase 1 early access runtime" in readme
    assert "local web console at `/console`" in readme
    assert "serves `/v1` plus the local web console at `/console`" in readme
    assert "No runtime implementation yet" not in readme
    assert "OpenAI-compatible speech stubs" not in readme
    assert "durable install lifecycle, packaging smoke" not in readme
