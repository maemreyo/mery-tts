from dataclasses import dataclass
from typing import Literal

type ProviderRolloutPhase = Literal[
    "planned",
    "platform-integrated",
    "audio-validated",
]
type ProviderRuntimeState = Literal[
    "missing_dependency",
    "missing_model",
    "installed_unhealthy",
    "audio_validated",
    "not_started",
]


@dataclass(frozen=True, slots=True)
class ProviderRolloutStatus:
    phase: ProviderRolloutPhase
    runtime_state: ProviderRuntimeState
    detail: str


def provider_rollout_status() -> dict[str, ProviderRolloutStatus]:
    return {
        "kokoro": ProviderRolloutStatus(
            phase="platform-integrated",
            runtime_state="missing_dependency",
            detail=(
                "Catalog, storage hydration, adapter seam, and marked real-runtime "
                "smoke exist; optional dependency/fixture validation is pending."
            ),
        ),
        "piper-plus": ProviderRolloutStatus(
            phase="platform-integrated",
            runtime_state="missing_dependency",
            detail=(
                "Catalog, storage hydration, adapter seam, and marked real-runtime "
                "smoke exist; optional dependency/fixture validation is pending."
            ),
        ),
        "supertonic": ProviderRolloutStatus(
            phase="planned",
            runtime_state="not_started",
            detail="Provider rollout not started.",
        ),
        "voxcpm2": ProviderRolloutStatus(
            phase="planned",
            runtime_state="not_started",
            detail="Provider rollout not started.",
        ),
    }


__all__ = ["ProviderRolloutStatus", "provider_rollout_status"]
