"""VoicePack install graph schema.

ADR-0027 — VoicePack install graph.

Introduces an explicit runtime install graph:

    VoicePack → Voice → Artifact → ProviderRuntime

VoicePacks are the primary user-facing install object.  Voices remain the
synthesis-time selectable identity.  Artifacts and provider runtimes remain
internal install/readiness dependencies.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProviderRuntimeRequirement(BaseModel):
    """A provider runtime that must be available before voices can synthesize."""

    model_config = ConfigDict(frozen=True)

    provider_runtime_id: str
    engine_id: str
    display_name: str
    install_mode: str = "unknown"


class VoicePackVoiceRef(BaseModel):
    """Reference from a VoicePack to a voice in the catalog graph."""

    model_config = ConfigDict(frozen=True)

    voice_id: str
    artifact_id: str
    engine_id: str


class VoicePack(BaseModel):
    """User-facing install unit grouping voices, artifacts, and runtime requirements.

    VoicePacks match user intent (e.g. "English reading", "Vietnamese offline voice")
    rather than raw model IDs or provider-specific identifiers.
    """

    model_config = ConfigDict(frozen=True)

    voice_pack_id: str
    display_name: str
    description: str = ""
    locale: str = ""
    use_case: str = ""
    voice_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    provider_runtime_ids: list[str] = Field(default_factory=list)
    estimated_size_bytes: int = 0
    recommended: bool = False

    @model_validator(mode="after")
    def validate_ids(self) -> VoicePack:
        if not self.voice_pack_id.strip():
            raise ValueError("voicePackId must not be empty")
        _reject_unsafe_id(self.voice_pack_id)
        for voice_id in self.voice_ids:
            _reject_unsafe_id(voice_id)
        for artifact_id in self.artifact_ids:
            _reject_unsafe_id(artifact_id)
        for runtime_id in self.provider_runtime_ids:
            _reject_unsafe_id(runtime_id)
        return self

    @property
    def total_size_display(self) -> str:
        if self.estimated_size_bytes <= 0:
            return "unknown"
        mb = self.estimated_size_bytes / (1024 * 1024)
        if mb >= 1024:
            return f"{mb / 1024:.1f} GB"
        return f"{mb:.0f} MB"


class VoicePackGraph(BaseModel):
    """Complete voice pack graph with validation for referential integrity.

    Extends the catalog graph with user-facing VoicePack nodes that reference
    voices, artifacts, and provider runtimes by ID.
    """

    model_config = ConfigDict(frozen=True)

    voice_packs: list[VoicePack] = Field(default_factory=list)
    provider_runtimes: list[ProviderRuntimeRequirement] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self) -> VoicePackGraph:
        pack_ids = [pack.voice_pack_id for pack in self.voice_packs]
        runtime_ids = {rt.provider_runtime_id for rt in self.provider_runtimes}

        if len(pack_ids) != len(set(pack_ids)):
            raise ValueError("duplicate voicePackId")

        for pack in self.voice_packs:
            for runtime_id in pack.provider_runtime_ids:
                if runtime_id not in runtime_ids:
                    raise ValueError(
                        f"voice pack {pack.voice_pack_id!r} references "
                        f"unknown provider runtime {runtime_id!r}"
                    )

        return self


def _reject_unsafe_id(identifier: str) -> None:
    """Reject identifiers that could be filesystem paths or URLs."""
    if not identifier.strip():
        raise ValueError("identifier must not be empty")
    lowered = identifier.lower()
    if lowered.startswith(("http://", "https://", "file://")):
        raise ValueError("identifier must not be a URL")
    if identifier.startswith("~"):
        raise ValueError("identifier must not be a filesystem path")
    if ".." in identifier or "/" in identifier or "\\" in identifier:
        raise ValueError("identifier must not be a filesystem path")
    if len(identifier) >= 2 and identifier[1] == ":":
        raise ValueError("identifier must not be a filesystem path")


def voice_packs_for_catalog_graph(
    *,
    voice_pack_graph: VoicePackGraph,
    installed_voice_ids: set[str],
    installed_runtime_ids: set[str] | None = None,
) -> list[dict[str, object]]:
    """Project voice packs with install/readiness status for API responses.

    Returns a list of dicts safe for client consumption — no raw filesystem
    paths or unsafe provider internals are exposed.
    """
    installed_runtimes = installed_runtime_ids or set()
    result: list[dict[str, object]] = []
    for pack in voice_pack_graph.voice_packs:
        voices_installed = sum(1 for vid in pack.voice_ids if vid in installed_voice_ids)
        total_voices = len(pack.voice_ids)
        runtimes_ready = all(rid in installed_runtimes for rid in pack.provider_runtime_ids)

        if voices_installed == total_voices and runtimes_ready:
            status = "installed"
        elif voices_installed > 0:
            status = "partial"
        elif not runtimes_ready and pack.provider_runtime_ids:
            status = "missing_runtime"
        else:
            status = "available"

        result.append(
            {
                "voice_pack_id": pack.voice_pack_id,
                "display_name": pack.display_name,
                "description": pack.description,
                "locale": pack.locale,
                "use_case": pack.use_case,
                "estimated_size_bytes": pack.estimated_size_bytes,
                "recommended": pack.recommended,
                "voice_ids": list(pack.voice_ids),
                "provider_runtime_ids": list(pack.provider_runtime_ids),
                "voices_installed": voices_installed,
                "voices_total": total_voices,
                "runtimes_ready": runtimes_ready,
                "status": status,
            }
        )
    return result


__all__ = [
    "ProviderRuntimeRequirement",
    "VoicePack",
    "VoicePackGraph",
    "VoicePackVoiceRef",
    "voice_packs_for_catalog_graph",
]
