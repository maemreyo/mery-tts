from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstallProgress:
    job_id: str
    model_id: str
    phase: str
    percent: int


@dataclass(frozen=True, slots=True)
class InstallDone:
    job_id: str
    model_id: str
    engine_id: str


@dataclass(frozen=True, slots=True)
class InstallFailed:
    job_id: str
    model_id: str
    error: str


type InstallEvent = InstallProgress | InstallDone | InstallFailed
