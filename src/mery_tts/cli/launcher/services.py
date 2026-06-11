from __future__ import annotations

import socket
import webbrowser
from collections.abc import Callable
from pathlib import Path

import uvicorn

from mery_tts.diagnostics.doctor import DoctorEngine
from mery_tts.help import get_help_topic, list_help_topics
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfig, HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.setup.intent import SetupIntent
from mery_tts.storage.identity import StorageIdentityStore

BrowserOpener = Callable[[str], bool]


def load_config(paths: RuntimePaths) -> HelperConfig:
    return HelperConfigStore(paths.config_dir).load_or_create()


def console_url(config: HelperConfig) -> str:
    return f"http://127.0.0.1:{config.port}/console"


def api_docs_url(config: HelperConfig) -> str:
    return f"http://127.0.0.1:{config.port}/docs"


def openapi_url(config: HelperConfig) -> str:
    return f"http://127.0.0.1:{config.port}/openapi.json"


def setup_url(config: HelperConfig, *, client: str = "mery-cli", intent: str = "general") -> str:
    return SetupIntent(client=client, intent=intent).to_console_url(
        base_url=f"http://127.0.0.1:{config.port}"
    )


def is_server_reachable(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def run_doctor_summary(paths: RuntimePaths) -> list[dict[str, str | None]]:
    results = DoctorEngine(data_dir=paths.base_dir).run()
    return [result.to_json() for result in results]


def installed_voice_count(paths: RuntimePaths) -> int:
    return len(StorageIdentityStore(paths.models_dir).hydrate_installed_voice_descriptors())


def storage_summary(paths: RuntimePaths) -> dict[str, object]:
    stats = ModelStore(paths.models_dir).disk_usage()
    return {
        "models_dir": str(stats.root_path),
        "used_bytes": stats.used_bytes,
        "available_bytes": stats.available_bytes,
    }


def create_pairing_challenge(paths: RuntimePaths) -> dict[str, object]:
    store = HelperConfigStore(paths.config_dir)
    config = store.load_or_create()
    challenge = PairingService(config_store=store, config=config).create_challenge()
    return {
        "pairing_code": challenge.code,
        "setup_url": challenge.setup_url,
        "expires_at": challenge.expires_at.isoformat(),
    }


def open_url(url: str, opener: BrowserOpener | None = None) -> bool:
    return (opener or webbrowser.open_new_tab)(url)


def local_help_topics() -> list[dict[str, str]]:
    return [{"topic_id": topic.topic_id, "title": topic.title} for topic in list_help_topics()]


def local_help_topic(topic_id: str) -> dict[str, str]:
    topic = get_help_topic(topic_id)
    return {"topic_id": topic.topic_id, "title": topic.title, "body": topic.body}


def path_summary(paths: RuntimePaths) -> dict[str, str]:
    return {
        "base_dir": str(paths.base_dir),
        "config_dir": str(paths.config_dir),
        "models_dir": str(paths.models_dir),
        "cache_dir": str(paths.cache_dir),
        "logs_dir": str(paths.logs_dir),
        "catalog_dir": str(paths.catalog_dir),
    }


def serve_foreground(paths: RuntimePaths) -> None:
    store = HelperConfigStore(paths.config_dir)
    config = store.load_or_create()
    store.record_bound_port(config.port)
    uvicorn.run(
        "mery_tts.api.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=config.port,
        log_level="info",
    )


def repo_path(repo_root: Path, *parts: str) -> Path:
    return repo_root.joinpath(*parts)
