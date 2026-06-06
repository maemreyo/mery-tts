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

    paths = RuntimePaths.from_environment()

    assert paths.base_dir == Path("/tmp/custom-mery")
    assert paths.config_dir == Path("/tmp/custom-mery/config")
    assert paths.models_dir == Path("/tmp/custom-mery/models")
    assert paths.cache_dir == Path("/tmp/custom-mery/cache")
    assert paths.logs_dir == Path("/tmp/custom-mery/logs")
    assert paths.catalog_dir == Path("/tmp/custom-mery/catalog")


def test_runtime_paths_never_use_package_relative_writable_dirs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MERY_TTS_DATA_DIR", raising=False)

    paths = RuntimePaths.from_environment()
    package_root = Path(__file__).resolve().parents[2]

    assert paths.base_dir != package_root
    assert package_root not in paths.base_dir.parents
    for runtime_dir in [
        paths.config_dir,
        paths.models_dir,
        paths.cache_dir,
        paths.logs_dir,
        paths.catalog_dir,
    ]:
        assert runtime_dir.is_relative_to(paths.base_dir)
        assert package_root not in runtime_dir.parents
