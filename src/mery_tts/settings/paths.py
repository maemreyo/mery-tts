import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_dir


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    base_dir: Path
    config_dir: Path
    models_dir: Path
    cache_dir: Path
    logs_dir: Path
    catalog_dir: Path

    @classmethod
    def from_base(cls, base_dir: Path) -> "RuntimePaths":
        return cls(
            base_dir=base_dir,
            config_dir=base_dir / "config",
            models_dir=base_dir / "models",
            cache_dir=base_dir / "cache",
            logs_dir=base_dir / "logs",
            catalog_dir=base_dir / "catalog",
        )

    @classmethod
    def from_environment(cls) -> "RuntimePaths":
        override = os.environ.get("MERY_TTS_DATA_DIR")
        base_dir = Path(override) if override else Path(user_data_dir("Mery TTS", "zaob-dev"))
        return cls.from_base(base_dir)
