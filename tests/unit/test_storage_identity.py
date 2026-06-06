import json
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


def test_hydrates_installed_voice_descriptors_from_manifests(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(engine_id="kokoro", artifact_id="artifact.af", metadata={})
    store.write_artifact_manifest(engine_id="piper-plus", artifact_id="artifact.vi", metadata={})
    store.write_voice_manifest(
        "voice.kokoro.af",
        ["artifact.af"],
        {"kind": "preset", "preset_id": "af_heart"},
    )
    store.write_voice_manifest(
        "voice.piper.vi",
        ["artifact.vi"],
        {"kind": "preset", "preset_id": "vi_demo"},
    )

    descriptors = store.hydrate_installed_voice_descriptors()

    assert [(voice.voice_id, voice.engine_id) for voice in descriptors] == [
        ("voice.kokoro.af", "kokoro"),
        ("voice.piper.vi", "piper-plus"),
    ]


def test_missing_artifact_diagnostic(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_voice_manifest(
        "voice.missing",
        ["missing"],
        {"kind": "preset", "preset_id": "x"},
    )

    with pytest.raises(ValueError, match="missing artifact"):
        store.hydrate_voice_descriptor("voice.missing", engine_id="kokoro")


def test_storage_identity_rejects_unsupported_payload_family(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(engine_id="kokoro", artifact_id="artifact.test", metadata={})
    store.voices_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = store.voices_dir / "voice.test.json"
    manifest_path.write_text(
        json.dumps(
            {
                "voiceId": "voice.test",
                "artifactRefs": ["artifact.test"],
                "payloadTemplate": {"kind": "unknown-family"},
            }
        )
    )

    with pytest.raises(ValueError, match="unsupported payload family"):
        store.hydrate_installed_voice_descriptors()


def test_storage_identity_rejects_duplicate_voice_ids(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(engine_id="kokoro", artifact_id="artifact.test", metadata={})
    store.voices_dir.mkdir(parents=True, exist_ok=True)
    manifest_path1 = store.voices_dir / "voice.test1.json"
    manifest_path1.write_text(
        json.dumps(
            {
                "voiceId": "voice.test",
                "artifactRefs": ["artifact.test"],
                "payloadTemplate": {"kind": "preset", "preset_id": "test1"},
            }
        )
    )
    manifest_path2 = store.voices_dir / "voice.test2.json"
    manifest_path2.write_text(
        json.dumps(
            {
                "voiceId": "voice.test",
                "artifactRefs": ["artifact.test"],
                "payloadTemplate": {"kind": "preset", "preset_id": "test2"},
            }
        )
    )

    with pytest.raises(ValueError, match="duplicate voice ID"):
        store.hydrate_installed_voice_descriptors()


def test_storage_identity_rejects_preset_missing_preset_id(tmp_path: Path) -> None:
    store = StorageIdentityStore(tmp_path)
    store.write_artifact_manifest(engine_id="kokoro", artifact_id="artifact.test", metadata={})
    store.voices_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = store.voices_dir / "voice.test.json"
    manifest_path.write_text(
        json.dumps(
            {
                "voiceId": "voice.test",
                "artifactRefs": ["artifact.test"],
                "payloadTemplate": {"kind": "preset"},
            }
        )
    )

    with pytest.raises(ValueError, match="preset payload missing preset_id"):
        store.hydrate_installed_voice_descriptors()


@pytest.mark.parametrize(
    "unsafe_id",
    [
        "../secret",
        "a/b",
        "a\\b",
        "/tmp/storage",
        "C:\\storage",
        "http://example.com/storage",
        "https://example.com/storage",
        "file:///tmp/storage",
        "~/storage",
        "~storage",
    ],
)
def test_storage_identity_rejects_unsafe_identifiers(unsafe_id: str) -> None:
    from mery_tts.security.guards import reject_unsafe_identifier

    with pytest.raises(ValueError):
        reject_unsafe_identifier(unsafe_id)
