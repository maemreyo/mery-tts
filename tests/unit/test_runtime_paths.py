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


def test_runtime_paths_override_propagates_to_all_runtime_components(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """End-to-end: MERY_TTS_DATA_DIR override propagates to all runtime components."""
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    from mery_tts.api.app import create_app
    from mery_tts.catalog import load_bundled_catalog
    from mery_tts.diagnostics.doctor import DoctorEngine
    from mery_tts.models.store import ModelStore
    from mery_tts.security.config import HelperConfigStore

    paths = RuntimePaths.from_environment()

    config_store = HelperConfigStore(paths.config_dir)
    config = config_store.load_or_create()
    assert config_store.config_path.is_relative_to(paths.config_dir)

    model_store = ModelStore(paths.models_dir)
    assert model_store.root_path.is_relative_to(paths.models_dir)

    catalog = load_bundled_catalog()
    assert catalog.catalog_id == "bundled-v1"

    doctor = DoctorEngine(data_dir=paths.base_dir)
    doctor.run()
    doctor_path = paths.base_dir / "diagnostics" / "last-doctor.json"
    assert doctor_path.exists()

    app = create_app(config=config)
    assert app is not None
