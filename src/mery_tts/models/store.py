import shutil
from dataclasses import dataclass
from pathlib import Path

from mery_tts.errors import (
    ErrorCategory,
    ErrorCode,
    ErrorRecoverability,
    ErrorSeverity,
    FallbackPolicy,
    LocalTTSError,
    RecommendedAction,
)


@dataclass(frozen=True, slots=True)
class InstalledModelRecord:
    engine_id: str
    model_id: str
    install_path: Path
    size_bytes: int


@dataclass(frozen=True, slots=True)
class StorageStats:
    root_path: Path
    used_bytes: int
    available_bytes: int | None


class ModelStore:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    def path_for(self, engine_id: str, model_id: str) -> Path:
        return self.root_path / engine_id / model_id

    def list_installed(self) -> list[InstalledModelRecord]:
        if not self.root_path.exists():
            return []
        records: list[InstalledModelRecord] = []
        for engine_dir in sorted(path for path in self.root_path.iterdir() if path.is_dir()):
            for model_dir in sorted(path for path in engine_dir.iterdir() if path.is_dir()):
                records.append(
                    InstalledModelRecord(
                        engine_id=engine_dir.name,
                        model_id=model_dir.name,
                        install_path=model_dir,
                        size_bytes=self._directory_size(model_dir),
                    )
                )
        return records

    def find(self, model_id: str) -> InstalledModelRecord | None:
        return next(
            (record for record in self.list_installed() if record.model_id == model_id),
            None,
        )

    def delete(self, engine_id: str, model_id: str) -> None:
        model_path = self.path_for(engine_id, model_id)
        if not model_path.exists():
            raise self._delete_failed(model_id, "model directory does not exist")
        try:
            shutil.rmtree(model_path)
        except OSError as exc:
            raise self._delete_failed(model_id, "model directory could not be removed") from exc

    def delete_by_model_id(self, model_id: str) -> bool:
        record = self.find(model_id)
        if record is None:
            return False
        self.delete(record.engine_id, record.model_id)
        return True

    def disk_usage(self) -> StorageStats:
        used_bytes = self._directory_size(self.root_path) if self.root_path.exists() else 0
        try:
            usage_path = self.root_path if self.root_path.exists() else self.root_path.parent
            usage = shutil.disk_usage(usage_path)
            available_bytes: int | None = usage.free
        except OSError:
            available_bytes = None
        return StorageStats(
            root_path=self.root_path,
            used_bytes=used_bytes,
            available_bytes=available_bytes,
        )

    def _directory_size(self, path: Path) -> int:
        if not path.exists():
            return 0
        return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())

    def _delete_failed(self, model_id: str, diagnostic: str) -> LocalTTSError:
        return LocalTTSError(
            code=ErrorCode.MODEL_DELETE_FAILED,
            category=ErrorCategory.MODEL,
            severity=ErrorSeverity.ERROR,
            recoverability=ErrorRecoverability.USER_ACTION,
            user_message_key="errors.model.delete_failed",
            recommended_action=RecommendedAction.RETRY,
            fallback_policy=FallbackPolicy.NONE,
            sanitized_diagnostic=f"model_id={model_id};reason={diagnostic}",
            request_id="local",
            timestamp=__import__("datetime").datetime.now(__import__("datetime").UTC),
        )
