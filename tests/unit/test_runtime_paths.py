from pathlib import Path

import pytest

from mery_tts.settings.paths import RuntimePaths


def test_runtime_paths_use_app_data_root() -> None:
    paths = RuntimePaths.from_base(Path("/tmp/mery-data"))

    assert paths.config_dir == Path("/tmp/mery-data/config")
    assert paths.models_dir == Path("/tmp/mery-data/models")
    assert paths.cache_dir == Path("/tmp/mery-data/cache")
    assert paths.logs_dir == Path("/tmp/mery-data/logs")
    assert paths.catalog_dir == Path("/tmp/mery-data/catalog")


def test_runtime_paths_support_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", "/tmp/custom-mery")

    assert RuntimePaths.from_environment().base_dir == Path("/tmp/custom-mery")
