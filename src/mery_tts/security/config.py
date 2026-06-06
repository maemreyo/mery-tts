import json
import os
import secrets
import uuid
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class HelperConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    helper_id: str = Field(min_length=1)
    auth_token: str = Field(min_length=32)
    port: int = Field(default=8765, ge=1, le=65535)
    bound_port: int | None = Field(default=None, ge=1, le=65535)


class HelperConfigStore:
    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir
        self.config_path = config_dir / "config.json"

    def load_or_create(self) -> HelperConfig:
        if self.config_path.exists():
            return HelperConfig.model_validate_json(self.config_path.read_text())

        config = HelperConfig(
            helper_id=f"mery-{uuid.uuid4().hex}",
            auth_token=secrets.token_urlsafe(32),
            port=self._configured_port(),
        )
        self._write(config)
        return config

    def record_bound_port(self, bound_port: int) -> HelperConfig:
        config = self.load_or_create().model_copy(update={"bound_port": bound_port})
        self._write(config)
        return config

    def rotate_token(self) -> HelperConfig:
        config = self.load_or_create().model_copy(update={"auth_token": secrets.token_urlsafe(32)})
        self._write(config)
        return config

    def _configured_port(self) -> int:
        raw_port = os.environ.get("MERY_TTS_PORT")
        if raw_port is None:
            return 8765
        return int(raw_port)

    def _write(self, config: HelperConfig) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        payload = config.model_dump(mode="json")
        serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        temp_path = self.config_path.with_name(f"{self.config_path.name}.tmp")
        try:
            temp_path.write_text(serialized)
            temp_path.chmod(0o600)
            temp_path.replace(self.config_path)
        except OSError as exc:
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"failed to write config: {exc}") from exc
