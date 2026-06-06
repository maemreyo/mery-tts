"""Install plan resolver for VoicePack graph (ADR-0027).

Resolves a VoicePack install request into a deterministic plan of provider
runtime checks, artifact install steps, voice manifest writes, and post-install
smoke targets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from mery_tts.catalog.normalized import CatalogGraph
from mery_tts.catalog.voice_pack import VoicePack, VoicePackGraph


class InstallPlanStepKind(StrEnum):
    """Kinds of steps in an install plan."""

    CHECK_PROVIDER_RUNTIME = "check_provider_runtime"
    INSTALL_ARTIFACT = "install_artifact"
    WRITE_VOICE_MANIFEST = "write_voice_manifest"
    SMOKE_TEST = "smoke_test"


@dataclass(frozen=True, slots=True)
class InstallPlanStep:
    """A single step in an install plan."""

    kind: InstallPlanStepKind
    target_id: str
    engine_id: str | None = None
    artifact_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InstallPlan:
    """Deterministic install plan for a VoicePack.

    The plan is resolved before any filesystem mutation. Invalid graph
    relationships fail before any step executes.
    """

    voice_pack_id: str
    steps: tuple[InstallPlanStep, ...]
    provider_runtime_ids: tuple[str, ...]
    artifact_ids: tuple[str, ...]
    voice_ids: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return len(self.steps) == 0


class InstallPlanError(Exception):
    """Error during install plan resolution."""

    def __init__(self, message: str, *, voice_pack_id: str | None = None) -> None:
        self.voice_pack_id = voice_pack_id
        super().__init__(message)


def resolve_install_plan(
    *,
    voice_pack_id: str,
    voice_pack_graph: VoicePackGraph,
    catalog_graph: CatalogGraph | None = None,
    installed_voice_ids: set[str] | None = None,
    installed_runtime_ids: set[str] | None = None,
) -> InstallPlan:
    """Resolve a VoicePack into a deterministic install plan.

    Args:
        voice_pack_id: The voice pack to install.
        voice_pack_graph: VoicePackGraph containing pack definitions.
        catalog_graph: Optional CatalogGraph for artifact metadata.
        installed_voice_ids: Already-installed voice IDs (skipped in plan).
        installed_runtime_ids: Already-installed runtime IDs (skipped in plan).

    Returns:
        Deterministic InstallPlan with ordered steps.

    Raises:
        InstallPlanError: If the voice pack is not found or graph is invalid.
    """
    installed_voices = installed_voice_ids or set()
    installed_runtimes = installed_runtime_ids or set()

    pack = None
    for p in voice_pack_graph.voice_packs:
        if p.voice_pack_id == voice_pack_id:
            pack = p
            break

    if pack is None:
        raise InstallPlanError(
            f"voice pack {voice_pack_id!r} not found",
            voice_pack_id=voice_pack_id,
        )

    steps: list[InstallPlanStep] = []

    # Phase 1: Check provider runtimes before any artifact install
    for runtime_id in pack.provider_runtime_ids:
        if runtime_id not in installed_runtimes:
            runtime = None
            for rt in voice_pack_graph.provider_runtimes:
                if rt.provider_runtime_id == runtime_id:
                    runtime = rt
                    break
            engine_id = runtime.engine_id if runtime else "unknown"
            steps.append(
                InstallPlanStep(
                    kind=InstallPlanStepKind.CHECK_PROVIDER_RUNTIME,
                    target_id=runtime_id,
                    engine_id=engine_id,
                    metadata={"display_name": runtime.display_name if runtime else runtime_id},
                )
            )

    # Phase 2: Install artifacts (shared artifacts installed once)
    seen_artifacts: set[str] = set()
    for artifact_id in pack.artifact_ids:
        if artifact_id not in seen_artifacts:
            seen_artifacts.add(artifact_id)
            engine_id = _resolve_artifact_engine(artifact_id, pack, catalog_graph)
            steps.append(
                InstallPlanStep(
                    kind=InstallPlanStepKind.INSTALL_ARTIFACT,
                    target_id=artifact_id,
                    engine_id=engine_id,
                    artifact_id=artifact_id,
                )
            )

    # Phase 3: Write voice manifests for voices not yet installed
    for voice_id in pack.voice_ids:
        if voice_id not in installed_voices:
            engine_id = _resolve_voice_engine(voice_id, pack, catalog_graph)
            voice_artifact_id = _resolve_voice_artifact(voice_id, pack, catalog_graph)
            steps.append(
                InstallPlanStep(
                    kind=InstallPlanStepKind.WRITE_VOICE_MANIFEST,
                    target_id=voice_id,
                    engine_id=engine_id,
                    artifact_id=voice_artifact_id,
                )
            )

    # Phase 4: Post-install smoke targets
    for voice_id in pack.voice_ids:
        engine_id = _resolve_voice_engine(voice_id, pack, catalog_graph)
        steps.append(
            InstallPlanStep(
                kind=InstallPlanStepKind.SMOKE_TEST,
                target_id=voice_id,
                engine_id=engine_id,
            )
        )

    return InstallPlan(
        voice_pack_id=voice_pack_id,
        steps=tuple(steps),
        provider_runtime_ids=tuple(pack.provider_runtime_ids),
        artifact_ids=tuple(pack.artifact_ids),
        voice_ids=tuple(pack.voice_ids),
    )


def _resolve_artifact_engine(
    artifact_id: str,
    pack: VoicePack,
    catalog_graph: CatalogGraph | None,
) -> str:
    if catalog_graph is not None:
        for artifact in catalog_graph.artifacts:
            if artifact.artifact_id == artifact_id:
                return str(artifact.engine_id)
    return _infer_engine_from_pack(pack)


def _resolve_voice_engine(
    voice_id: str,
    pack: VoicePack,
    catalog_graph: CatalogGraph | None,
) -> str:
    if catalog_graph is not None:
        for voice in catalog_graph.voices:
            if voice.voice_id == voice_id:
                return str(voice.engine_id)
    return _infer_engine_from_pack(pack)


def _resolve_voice_artifact(
    voice_id: str,
    pack: VoicePack,
    catalog_graph: CatalogGraph | None,
) -> str | None:
    if catalog_graph is not None:
        for voice in catalog_graph.voices:
            if voice.voice_id == voice_id:
                return str(voice.artifact_id)
    return str(pack.artifact_ids[0]) if pack.artifact_ids else None


def _infer_engine_from_pack(pack: VoicePack) -> str:
    """Infer engine_id from pack's provider_runtime_ids or voice_ids."""
    if pack.provider_runtime_ids:
        runtime_id = pack.provider_runtime_ids[0]
        if "piper" in runtime_id.lower():
            return "piper-plus"
        if "kokoro" in runtime_id.lower():
            return "kokoro"
    if pack.voice_ids:
        first_voice = pack.voice_ids[0]
        if "piper" in first_voice.lower():
            return "piper-plus"
        if "kokoro" in first_voice.lower():
            return "kokoro"
    return "unknown"


__all__ = [
    "InstallPlan",
    "InstallPlanError",
    "InstallPlanStep",
    "InstallPlanStepKind",
    "resolve_install_plan",
]
