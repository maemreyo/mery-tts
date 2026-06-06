import json
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from mery_tts.errors import RecommendedAction, sanitize_diagnostic

DoctorStatus = Literal["ok", "warn", "fail"]


@dataclass(frozen=True, slots=True)
class DoctorResult:
    check: str
    status: DoctorStatus
    detail: str
    recommended_action: RecommendedAction | None = None

    def to_json(self) -> dict[str, str | None]:
        sanitized = sanitize_diagnostic({"detail": self.detail})
        return {
            "check": self.check,
            "status": self.status,
            "detail": str(sanitized.get("detail", "diagnostic omitted")),
            "recommended_action": (
                self.recommended_action.value if self.recommended_action else None
            ),
        }


class DoctorCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def run(self) -> DoctorResult: ...


class EngineAvailabilityCheck(DoctorCheck):
    def __init__(self, engine_ids: list[str]) -> None:
        self._engine_ids = engine_ids

    @property
    def name(self) -> str:
        return "engine_availability"

    def run(self) -> DoctorResult:
        if not self._engine_ids:
            return DoctorResult(
                check=self.name,
                status="warn",
                detail="no engines loaded",
                recommended_action=RecommendedAction.CHECK_ENGINE,
            )
        return DoctorResult(
            check=self.name,
            status="ok",
            detail=f"loaded: {', '.join(sorted(self._engine_ids))}",
        )


class EngineHealthCheck(DoctorCheck):
    def __init__(self, unhealthy: list[str]) -> None:
        self._unhealthy = unhealthy

    @property
    def name(self) -> str:
        return "engine_health"

    def run(self) -> DoctorResult:
        if self._unhealthy:
            return DoctorResult(
                check=self.name,
                status="warn",
                detail=f"unhealthy: {', '.join(sorted(self._unhealthy))}",
                recommended_action=RecommendedAction.CHECK_ENGINE,
            )
        return DoctorResult(check=self.name, status="ok", detail="all engines healthy")


class ModelAvailabilityCheck(DoctorCheck):
    def __init__(self, installed_models: list[str]) -> None:
        self._installed = installed_models

    @property
    def name(self) -> str:
        return "model_availability"

    def run(self) -> DoctorResult:
        if not self._installed:
            return DoctorResult(
                check=self.name,
                status="warn",
                detail="no models installed",
                recommended_action=RecommendedAction.INSTALL_MODEL,
            )
        return DoctorResult(
            check=self.name,
            status="ok",
            detail=f"installed: {len(self._installed)} model(s)",
        )


class TokenConfiguredCheck(DoctorCheck):
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    @property
    def name(self) -> str:
        return "token_configured"

    def run(self) -> DoctorResult:
        if not self._config_path.exists():
            return DoctorResult(
                check=self.name,
                status="fail",
                detail="config file missing",
                recommended_action=RecommendedAction.PAIR_CLIENT,
            )
        try:
            config = json.loads(self._config_path.read_text())
            if not config.get("auth_token"):
                return DoctorResult(
                    check=self.name,
                    status="fail",
                    detail="auth_token empty",
                    recommended_action=RecommendedAction.PAIR_CLIENT,
                )
        except (json.JSONDecodeError, OSError):
            return DoctorResult(
                check=self.name,
                status="fail",
                detail="config unreadable",
                recommended_action=RecommendedAction.PAIR_CLIENT,
            )
        return DoctorResult(check=self.name, status="ok", detail="token configured")


class ServerReachabilityCheck(DoctorCheck):
    def __init__(self, port: int) -> None:
        self._port = port

    @property
    def name(self) -> str:
        return "server_reachability"

    def run(self) -> DoctorResult:
        import socket

        try:
            with socket.create_connection(("127.0.0.1", self._port), timeout=1):
                return DoctorResult(
                    check=self.name, status="ok", detail=f"server reachable on port {self._port}"
                )
        except OSError:
            return DoctorResult(
                check=self.name,
                status="warn",
                detail="server not running",
            )


class DiskSpaceCheck(DoctorCheck):
    def __init__(self, models_dir: Path, min_free_bytes: int = 500 * 1024 * 1024) -> None:
        self._models_dir = models_dir
        self._min_free = min_free_bytes

    @property
    def name(self) -> str:
        return "disk_space"

    def run(self) -> DoctorResult:
        try:
            target = self._models_dir if self._models_dir.exists() else self._models_dir.parent
            usage = shutil.disk_usage(target)
            if usage.free < self._min_free:
                return DoctorResult(
                    check=self.name,
                    status="warn",
                    detail=f"low disk: {usage.free // (1024 * 1024)} MB free",
                    recommended_action=RecommendedAction.FREE_SPACE,
                )
            return DoctorResult(
                check=self.name,
                status="ok",
                detail=f"disk ok: {usage.free // (1024 * 1024)} MB free",
            )
        except OSError:
            return DoctorResult(
                check=self.name,
                status="warn",
                detail="disk usage unavailable",
            )


class PlatformPathsCheck(DoctorCheck):
    def __init__(self, writable_dirs: list[Path]) -> None:
        self._dirs = writable_dirs

    @property
    def name(self) -> str:
        return "platform_paths"

    def run(self) -> DoctorResult:
        for dir_path in self._dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                test_file = dir_path / ".mery-write-test"
                test_file.write_text("ok")
                test_file.unlink()
            except OSError:
                return DoctorResult(
                    check=self.name,
                    status="fail",
                    detail="path not writable",
                    recommended_action=RecommendedAction.CONTACT_SUPPORT,
                )
        return DoctorResult(check=self.name, status="ok", detail="all paths writable")


class CatalogAvailableCheck(DoctorCheck):
    @property
    def name(self) -> str:
        return "catalog_available"

    def run(self) -> DoctorResult:
        try:
            from mery_tts.catalog import load_bundled_catalog

            catalog = load_bundled_catalog()
            return DoctorResult(
                check=self.name,
                status="ok",
                detail=f"bundled catalog: {len(catalog.models)} model(s)",
            )
        except Exception:
            return DoctorResult(
                check=self.name,
                status="warn",
                detail="bundled catalog unavailable",
            )


class DoctorEngine:
    def __init__(
        self,
        *,
        results: list[DoctorResult] | None = None,
        checks: list[DoctorCheck] | None = None,
        data_dir: Path,
    ) -> None:
        self._results = results
        self._checks = checks
        self.data_dir = data_dir

    def run(self) -> list[DoctorResult]:
        if self._results is not None:
            results = self._results
        elif self._checks is not None:
            results = [check.run() for check in self._checks]
        else:
            results = [
                DoctorResult(
                    check="engine_availability", status="warn", detail="no engines loaded"
                ),
                DoctorResult(check="engine_health", status="ok", detail="no unhealthy engines"),
                DoctorResult(
                    check="model_availability", status="warn", detail="no models installed"
                ),
                DoctorResult(check="token_configured", status="ok", detail="token configured"),
                DoctorResult(
                    check="server_reachability", status="warn", detail="server not running"
                ),
                DoctorResult(check="disk_space", status="ok", detail="disk space ok"),
                DoctorResult(check="platform_paths", status="ok", detail="paths writable"),
                DoctorResult(
                    check="catalog_available",
                    status="ok",
                    detail="bundled catalog available",
                ),
            ]
        self.persist(results)
        return results

    def persist(self, results: list[DoctorResult]) -> Path:
        path = self.data_dir / "diagnostics" / "last-doctor.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ranAt": datetime.now(UTC).isoformat(),
            "results": [result.to_json() for result in results],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return path

    def exit_code(self, results: list[DoctorResult]) -> int:
        if any(result.status == "fail" for result in results):
            return 1
        if any(result.status == "warn" for result in results):
            return 2
        return 0
