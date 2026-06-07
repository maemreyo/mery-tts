"""Installed voice resolver — converts manifest descriptors into resolved read-only payloads.

ADR-0024: InstalledVoiceResolver validates safe relative paths from voice manifests under
known artifact roots and returns immutable resolved voice objects for engine adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mery_tts.voice.descriptor import (
    ModelFileVoicePayload,
    PresetVoicePayload,
    VoiceDescriptor,
)


class VoiceResolutionError(ValueError):
    """Raised when a voice descriptor cannot be resolved to safe absolute paths."""


@dataclass(frozen=True, slots=True)
class ResolvedModelFilePayload:
    """Resolved model-file payload with validated absolute paths.

    ``native_sample_rate_hz`` is read from the config JSON during
    resolution and cached on the payload so downstream consumers
    (engine adapters, capability endpoints, HTTP transport) do not
    need to re-read or re-parse the config. ``None`` means the rate
    could not be determined; callers should fall back to the engine
    baseline.
    """

    artifact_id: str
    model_path: Path
    config_path: Path | None = None
    native_sample_rate_hz: int | None = None


@dataclass(frozen=True, slots=True)
class ResolvedPresetPayload:
    """Resolved preset payload with validated absolute artifact directory."""

    artifact_id: str
    preset_id: str
    artifact_dir: Path


type ResolvedVoicePayload = ResolvedModelFilePayload | ResolvedPresetPayload


@dataclass(frozen=True, slots=True)
class ResolvedVoice:
    """Immutable resolved voice with validated absolute paths for engine adapters."""

    voice_id: str
    engine_id: str
    payload: ResolvedVoicePayload


def _validate_safe_relative_path(relative_path: str) -> str:
    """Validate that a relative path cannot escape its root via traversal."""
    if not relative_path or not relative_path.strip():
        raise VoiceResolutionError("empty relative path")
    parts = Path(relative_path).parts
    if any(part == ".." for part in parts):
        raise VoiceResolutionError(f"path traversal detected: {relative_path}")
    if Path(relative_path).is_absolute():
        raise VoiceResolutionError(f"absolute path not allowed: {relative_path}")
    if "\\" in relative_path:
        raise VoiceResolutionError(f"windows path separator not allowed: {relative_path}")
    return relative_path


def _resolve_under_root(artifact_root: Path, relative_path: str) -> Path:
    """Resolve a relative path under an artifact root and verify it stays within."""
    _validate_safe_relative_path(relative_path)
    resolved = (artifact_root / relative_path).resolve()
    root_resolved = artifact_root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise VoiceResolutionError(f"resolved path escapes artifact root: {relative_path}") from exc
    return resolved


def _find_artifact_root(
    *,
    artifacts_dir: Path,
    engine_id: str,
    artifact_id: str,
) -> Path:
    """Find and validate the artifact directory for a given engine/artifact pair."""
    artifact_dir = artifacts_dir / engine_id / artifact_id
    if not artifact_dir.is_dir():
        raise VoiceResolutionError(f"missing artifact directory: {engine_id}/{artifact_id}")
    return artifact_dir


def _resolve_model_file(
    voice: VoiceDescriptor,
    *,
    artifacts_dir: Path,
) -> ResolvedModelFilePayload:
    """Resolve a model-file voice descriptor to absolute paths."""
    if not isinstance(voice.payload, ModelFileVoicePayload):
        raise VoiceResolutionError("expected model-file payload")

    artifact_dir = _find_artifact_root(
        artifacts_dir=artifacts_dir,
        engine_id=voice.engine_id,
        artifact_id=voice.payload.artifact_id,
    )

    model_path = _resolve_under_root(artifact_dir, voice.payload.relative_path)
    if not model_path.is_file():
        raise VoiceResolutionError(f"model file not found: {voice.payload.relative_path}")

    config_path: Path | None = None
    config_relative = _infer_config_path(voice.payload.relative_path)
    if config_relative is not None:
        candidate = _resolve_under_root(artifact_dir, config_relative)
        if candidate.is_file():
            config_path = candidate

    native_sample_rate_hz = _read_native_sample_rate_hz(config_path) if config_path else None

    return ResolvedModelFilePayload(
        artifact_id=voice.payload.artifact_id,
        model_path=model_path,
        config_path=config_path,
        native_sample_rate_hz=native_sample_rate_hz,
    )


def _read_native_sample_rate_hz(config_path: Path) -> int | None:
    """Read ``sample_rate`` from a Piper config JSON, descending into ``audio`` first.

    The reader is a thin wrapper around the engine-specific config
    reader; it is imported lazily so the voice resolver module stays
    engine-agnostic and import-cheap.
    """
    try:
        from mery_tts.engines.piper_plus.config import PiperConfigReader
    except ImportError:
        return None
    return PiperConfigReader().read_sample_rate_hz(config_path)


def _infer_config_path(model_relative_path: str) -> str | None:
    """Infer a config file path from a model file path (e.g., .onnx → .onnx.json)."""
    if model_relative_path.endswith(".onnx"):
        return model_relative_path + ".json"
    return None


def _resolve_preset(
    voice: VoiceDescriptor,
    *,
    artifacts_dir: Path,
) -> ResolvedPresetPayload:
    """Resolve a preset voice descriptor to an absolute artifact directory."""
    if not isinstance(voice.payload, PresetVoicePayload):
        raise VoiceResolutionError("expected preset payload")

    artifact_dir = _find_artifact_root(
        artifacts_dir=artifacts_dir,
        engine_id=voice.engine_id,
        artifact_id=voice.payload.artifact_id  # pyright: ignore[reportAttributeAccessIssue]
        if hasattr(voice.payload, "artifact_id")
        else voice.payload.preset_id,
    )

    return ResolvedPresetPayload(
        artifact_id=voice.payload.preset_id,
        preset_id=voice.payload.preset_id,
        artifact_dir=artifact_dir,
    )


class InstalledVoiceResolver:
    """Resolves manifest-level VoiceDescriptor records into resolved read-only payloads.

    The resolver validates safe relative paths under known artifact roots and returns
    immutable ResolvedVoice objects. It rejects traversal, missing artifacts, missing
    files, ambiguous artifacts, and unsupported payload families.
    """

    SUPPORTED_PAYLOAD_KINDS = frozenset({"model-file", "preset"})

    def __init__(self, *, artifacts_dir: Path) -> None:
        self._artifacts_dir = artifacts_dir

    @property
    def artifacts_dir(self) -> Path:
        return self._artifacts_dir

    def resolve(self, voice: VoiceDescriptor) -> ResolvedVoice:
        """Resolve a voice descriptor into a ResolvedVoice with validated absolute paths."""
        kind = voice.payload.kind
        if kind not in self.SUPPORTED_PAYLOAD_KINDS:
            raise VoiceResolutionError(
                f"unsupported payload family '{kind}' for voice '{voice.voice_id}'"
            )

        if kind == "model-file":
            payload: ResolvedVoicePayload = _resolve_model_file(
                voice, artifacts_dir=self._artifacts_dir
            )
        elif kind == "preset":
            payload = _resolve_preset(voice, artifacts_dir=self._artifacts_dir)
        else:
            raise VoiceResolutionError(f"unhandled payload kind: {kind}")

        return ResolvedVoice(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            payload=payload,
        )

    def try_resolve(self, voice: VoiceDescriptor) -> ResolvedVoice | None:
        """Attempt to resolve a voice, returning None on failure instead of raising."""
        try:
            return self.resolve(voice)
        except VoiceResolutionError:
            return None


__all__ = [
    "InstalledVoiceResolver",
    "ResolvedModelFilePayload",
    "ResolvedPresetPayload",
    "ResolvedVoice",
    "ResolvedVoicePayload",
    "VoiceResolutionError",
]
