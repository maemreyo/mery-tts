from pathlib import Path

import pytest

from mery_tts.storage.identity import StorageIdentityStore, safe_voice_filename


def test_artifact_and_voice_manifest_layout(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)

    store.write_artifact_manifest(
        engine_id="kokoro",
        artifact_id="artifact.shared",
        metadata={"sha256": "0" * 64},
    )
    store.write_voice_manifest(
        voice_id="voice/kokoro.af",
        artifact_refs=["artifact.shared"],
        payload_template={"kind": "preset", "preset_id": "af_heart"},
    )

    assert (tmp_path / "artifacts" / "kokoro" / "artifact.shared" / "artifact.json").exists()
    voice_path = tmp_path / "voices" / safe_voice_filename("voice/kokoro.af")
    assert voice_path.exists()
    assert "/" not in voice_path.name
    assert "artifact.shared" in voice_path.read_text()


def test_shared_artifact_gc_only_removes_unreferenced_artifacts(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(engine_id="kokoro", artifact_id="artifact.shared", metadata={})
    store.write_voice_manifest(
        "voice.one",
        ["artifact.shared"],
        {"kind": "preset", "preset_id": "one"},
    )
    store.write_voice_manifest(
        "voice.two",
        ["artifact.shared"],
        {"kind": "preset", "preset_id": "two"},
    )

    assert store.delete_voice_and_collect_garbage("voice.one") == []
    assert store.delete_voice_and_collect_garbage("voice.two") == ["artifact.shared"]


def test_missing_artifact_diagnostic(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_voice_manifest(
        "voice.missing",
        ["missing"],
        {"kind": "preset", "preset_id": "x"},
    )

    with pytest.raises(ValueError, match="missing artifact"):
        store.hydrate_voice_descriptor("voice.missing", engine_id="kokoro")
