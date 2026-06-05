import json
import re
import shutil
from pathlib import Path
from typing import Any, cast

from mery_tts.voice import PresetVoicePayload, VoiceDescriptor


def safe_voice_filename(voice_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", voice_id) + ".json"


class StorageIdentityStore:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.artifacts_dir = root_path / "artifacts"
        self.voices_dir = root_path / "voices"

    def write_artifact_manifest(
        self,
        *,
        engine_id: str,
        artifact_id: str,
        metadata: dict[str, Any],
    ) -> Path:
        artifact_dir = self.artifacts_dir / engine_id / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = artifact_dir / "artifact.json"
        manifest = {"artifactId": artifact_id, "engineId": engine_id, **metadata}
        manifest_path.write_text(json.dumps(manifest, sort_keys=True))
        return manifest_path

    def write_voice_manifest(
        self,
        voice_id: str,
        artifact_refs: list[str],
        payload_template: dict[str, Any],
    ) -> Path:
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.voices_dir / safe_voice_filename(voice_id)
        manifest_path.write_text(
            json.dumps(
                {
                    "voiceId": voice_id,
                    "artifactRefs": artifact_refs,
                    "payloadTemplate": payload_template,
                },
                sort_keys=True,
            )
        )
        return manifest_path

    def hydrate_voice_descriptor(self, voice_id: str, *, engine_id: str) -> VoiceDescriptor:
        manifest = self._voice_manifest(voice_id)
        artifact_refs = manifest["artifactRefs"]
        for artifact_ref in artifact_refs:
            if not self._artifact_exists(engine_id=engine_id, artifact_id=artifact_ref):
                raise ValueError(f"missing artifact '{artifact_ref}'")
        payload_template = manifest["payloadTemplate"]
        if payload_template.get("kind") != "preset":
            raise ValueError("unsupported payload template")
        return VoiceDescriptor(
            voice_id=voice_id,
            engine_id=engine_id,
            payload=PresetVoicePayload(preset_id=str(payload_template["preset_id"])),
        )

    def delete_voice_and_collect_garbage(self, voice_id: str) -> list[str]:
        manifest_path = self.voices_dir / safe_voice_filename(voice_id)
        if not manifest_path.exists():
            return []
        manifest = json.loads(manifest_path.read_text())
        artifact_refs = list(manifest["artifactRefs"])
        manifest_path.unlink()
        live_refs = self._live_artifact_refs()
        collected: list[str] = []
        for artifact_id in artifact_refs:
            if artifact_id in live_refs:
                continue
            for artifact_dir in self.artifacts_dir.glob(f"*/{artifact_id}"):
                shutil.rmtree(artifact_dir)
                collected.append(artifact_id)
        return collected

    def _voice_manifest(self, voice_id: str) -> dict[str, Any]:
        loaded = json.loads((self.voices_dir / safe_voice_filename(voice_id)).read_text())
        return cast("dict[str, Any]", loaded)

    def _artifact_exists(self, *, engine_id: str, artifact_id: str) -> bool:
        return (self.artifacts_dir / engine_id / artifact_id / "artifact.json").exists()

    def _live_artifact_refs(self) -> set[str]:
        refs: set[str] = set()
        if not self.voices_dir.exists():
            return refs
        for path in self.voices_dir.glob("*.json"):
            manifest = json.loads(path.read_text())
            refs.update(manifest["artifactRefs"])
        return refs
