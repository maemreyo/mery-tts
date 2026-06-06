import shutil
from pathlib import Path

import pytest

from mery_tts.errors import ErrorCode, LocalTTSError
from mery_tts.models.store import ModelStore


def test_model_store_lists_empty_store(tmp_path: Path) -> None:
    store = ModelStore(tmp_path)

    assert store.list_installed() == []


def test_model_store_lists_installed_models_with_size(tmp_path: Path) -> None:
    model_dir = tmp_path / "piper-plus" / "piper-plus.en-us.demo"
    model_dir.mkdir(parents=True)
    (model_dir / "model.onnx").write_bytes(b"1234")

    records = ModelStore(tmp_path).list_installed()

    assert len(records) == 1
    assert records[0].engine_id == "piper-plus"
    assert records[0].model_id == "piper-plus.en-us.demo"
    assert records[0].size_bytes == 4


def test_model_store_deletes_existing_model(tmp_path: Path) -> None:
    model_dir = tmp_path / "kokoro" / "kokoro.en-us.demo"
    model_dir.mkdir(parents=True)
    (model_dir / "voice.bin").write_bytes(b"voice")

    ModelStore(tmp_path).delete("kokoro", "kokoro.en-us.demo")

    assert not model_dir.exists()


def test_model_store_delete_nonexistent_model_raises_structured_error(tmp_path: Path) -> None:
    with pytest.raises(LocalTTSError) as error:
        ModelStore(tmp_path).delete("kokoro", "missing")

    assert error.value.code == ErrorCode.MODEL_DELETE_FAILED


def test_model_store_delete_by_model_id_is_idempotent_for_missing_model(tmp_path: Path) -> None:
    assert ModelStore(tmp_path).delete_by_model_id("missing") is False


def test_model_store_delete_permission_failure_raises_structured_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_dir = tmp_path / "kokoro" / "kokoro.en-us.demo"
    model_dir.mkdir(parents=True)

    def fail_rmtree(path: Path) -> None:
        _ = path
        raise PermissionError("denied")

    monkeypatch.setattr(shutil, "rmtree", fail_rmtree)

    with pytest.raises(LocalTTSError) as error:
        ModelStore(tmp_path).delete("kokoro", "kokoro.en-us.demo")

    assert error.value.code == ErrorCode.MODEL_DELETE_FAILED


def test_model_store_storage_stats_empty_and_non_empty(tmp_path: Path) -> None:
    empty = ModelStore(tmp_path).disk_usage()
    model_dir = tmp_path / "kokoro" / "kokoro.en-us.demo"
    model_dir.mkdir(parents=True)
    (model_dir / "voice.bin").write_bytes(b"123")
    non_empty = ModelStore(tmp_path).disk_usage()

    assert empty.used_bytes == 0
    assert non_empty.used_bytes == 3
    assert non_empty.root_path == tmp_path
