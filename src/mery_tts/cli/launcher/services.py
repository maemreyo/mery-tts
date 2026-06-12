from __future__ import annotations

import contextlib
import json
import os
import secrets
import signal
import socket
import subprocess
import sys
import webbrowser
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import uvicorn

from mery_tts.catalog.bundled import load_bundled_catalog
from mery_tts.cli.suggestions import CommandSuggestion, format_human_suggestions
from mery_tts.diagnostics.doctor import DoctorEngine
from mery_tts.diagnostics.export import DiagnosticsExportBuilder
from mery_tts.diagnostics.recovery import ReadinessBlocker, recovery_action_for
from mery_tts.help import get_help_topic, list_help_topics
from mery_tts.jobs import FileInstallJobStore, InstallJobService
from mery_tts.models.store import ModelStore
from mery_tts.readiness.manifest import build_capability_readiness_manifest
from mery_tts.release import release_guidance
from mery_tts.runtime_policy import appliance_runtime_policy
from mery_tts.security.config import HelperConfig, HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.setup.intent import SetupIntent
from mery_tts.storage.identity import StorageIdentityStore

BrowserOpener = Callable[[str], bool]
ReadinessStatus = Literal["ready", "degraded", "blocked"]
SERVER_SESSION_FILENAME = "server-session.json"
SERVER_SESSION_ID_ENV = "MERY_TTS_LAUNCHER_SESSION_ID"


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


def print_pre_blocking_suggestions(suggestions: tuple[CommandSuggestion, ...]) -> None:
    message = format_human_suggestions(suggestions, title="Next, in another terminal")
    if message:
        print(message)


def is_server_reachable(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def server_session_path(paths: RuntimePaths) -> Path:
    return paths.base_dir / "launcher" / SERVER_SESSION_FILENAME


def load_server_session(paths: RuntimePaths) -> dict[str, object] | None:
    path = server_session_path(paths)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def server_session_status(paths: RuntimePaths) -> dict[str, object]:
    config = load_config(paths)
    reachable = is_server_reachable(config.port)
    session = load_server_session(paths)
    owned_pid = _session_pid(session)
    owned_running = _session_is_running(session)
    owner = "launcher" if owned_running else "external" if reachable else "none"
    return {
        "reachable": reachable,
        "host": "127.0.0.1",
        "port": config.port,
        "url": f"http://127.0.0.1:{config.port}",
        "owner": owner,
        "owned_pid": owned_pid if owned_running else None,
        "can_stop": owned_running,
    }


def start_session_server(paths: RuntimePaths) -> dict[str, object]:
    status = server_session_status(paths)
    if status["reachable"]:
        return {**status, "started": False, "reason": "already_reachable"}

    config = load_config(paths)
    paths.base_dir.mkdir(parents=True, exist_ok=True)
    log_dir = paths.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "launcher-server.log"
    log_handle = log_path.open("a")
    env = os.environ.copy()
    session_id = secrets.token_urlsafe(16)
    env["MERY_TTS_DATA_DIR"] = str(paths.base_dir)
    env["MERY_TTS_PORT"] = str(config.port)
    env[SERVER_SESSION_ID_ENV] = session_id
    process = subprocess.Popen(
        (sys.executable, "-m", "mery_tts.cli.main", "serve"),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    log_handle.close()
    session: dict[str, object] = {
        "pid": process.pid,
        "host": "127.0.0.1",
        "port": config.port,
        "started_at": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "log": "launcher-server.log",
    }
    _write_server_session(paths, session)
    return {
        "reachable": False,
        "host": "127.0.0.1",
        "port": config.port,
        "url": f"http://127.0.0.1:{config.port}",
        "owner": "launcher",
        "owned_pid": process.pid,
        "can_stop": True,
        "started": True,
        "log": "launcher-server.log",
    }


def stop_session_server(paths: RuntimePaths) -> dict[str, object]:
    session = load_server_session(paths)
    pid = _session_pid(session)
    if pid is None:
        return {**server_session_status(paths), "stopped": False, "reason": "no_owned_session"}
    if not _session_is_running(session):
        _remove_server_session(paths)
        return {**server_session_status(paths), "stopped": False, "reason": "owned_process_exited"}
    os.kill(pid, signal.SIGTERM)
    _remove_server_session(paths)
    status = server_session_status(paths)
    return {**status, "stopped": True, "stopped_pid": pid}


def _write_server_session(paths: RuntimePaths, payload: dict[str, object]) -> None:
    path = server_session_path(paths)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary_path.replace(path)


def _remove_server_session(paths: RuntimePaths) -> None:
    with contextlib.suppress(FileNotFoundError):
        server_session_path(paths).unlink()


def _session_pid(session: dict[str, object] | None) -> int | None:
    if session is None:
        return None
    pid = session.get("pid")
    return pid if isinstance(pid, int) and pid > 0 else None


def _session_id(session: dict[str, object] | None) -> str | None:
    if session is None:
        return None
    value = session.get("session_id")
    return value if isinstance(value, str) and value else None


def _session_is_running(session: dict[str, object] | None) -> bool:
    pid = _session_pid(session)
    session_id = _session_id(session)
    if pid is None or session_id is None:
        return False
    return _pid_is_running(pid) and _process_has_launcher_session(pid, session_id)


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _process_has_launcher_session(pid: int, session_id: str) -> bool:
    if os.name == "posix":
        environ_path = Path(f"/proc/{pid}/environ")
        with contextlib.suppress(OSError):
            environ = environ_path.read_bytes().split(b"\x00")
            expected = f"{SERVER_SESSION_ID_ENV}={session_id}".encode()
            return expected in environ
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


def bundled_baseline_install_metadata() -> dict[str, object]:
    catalog = load_bundled_catalog()
    baseline = next(
        (
            model
            for model in catalog.models
            if model.engine_id == "piper-plus" and model.locale == "en-US"
        ),
        None,
    )
    if baseline is None:
        return {
            "available": False,
            "recovery_action": "catalog.baseline_missing",
        }

    approximate_size = sum(file.size_bytes for file in baseline.files)
    provenance = baseline.provenance or baseline.source
    return {
        "available": True,
        "pack_id": "pack.en-us",
        "model_id": baseline.model_id,
        "provider": baseline.engine_id,
        "locale": baseline.locale,
        "source_kind": baseline.source,
        "approximate_size_bytes": approximate_size,
        "license": baseline.license,
        "provenance": provenance,
        "capability_impact": "Enables the P1 English local speech happy path.",
        "catalog_id": catalog.catalog_id,
        "remote_refresh_performed": False,
    }


def start_bundled_baseline_install(paths: RuntimePaths) -> dict[str, object]:
    metadata = bundled_baseline_install_metadata()
    if not metadata.get("available"):
        return metadata

    model_id = str(metadata["model_id"])
    provider = str(metadata["provider"])
    store = StorageIdentityStore(paths.models_dir)
    model_store = ModelStore(paths.models_dir)
    job_service = InstallJobService(
        store=store,
        refresh=lambda: None,
        job_store=FileInstallJobStore(model_store.root_path / "jobs" / "install"),
    )
    job = job_service.start_install(
        catalog_entry_id=model_id,
        voice_id=model_id,
        engine_id=provider,
        artifact_id=model_id,
    )
    return {
        **metadata,
        "job_id": job.job_id,
        "job_status": job.status.value,
        "poll_action": "models.install.status",
    }


def readiness_summary(paths: RuntimePaths) -> dict[str, object]:
    config = load_config(paths)
    reachable = is_server_reachable(config.port)
    doctor_results = run_doctor_summary(paths)
    voice_count = installed_voice_count(paths)
    storage = storage_summary(paths)
    failing = [result for result in doctor_results if result["status"] == "fail"]
    warnings = [result for result in doctor_results if result["status"] == "warn"]
    if failing:
        status: ReadinessStatus = "blocked"
    elif warnings or not reachable or voice_count == 0:
        status = "degraded"
    else:
        status = "ready"
    available_bytes = storage["available_bytes"]
    storage_writable = not isinstance(available_bytes, int) or available_bytes > 0
    pairing = pairing_status(paths)
    recovery_actions = _readiness_recovery_actions(
        reachable=reachable,
        auth_configured=bool(config.auth_token),
        voice_count=voice_count,
        storage_writable=storage_writable,
        doctor_results=doctor_results,
    )
    next_steps = _next_steps_for_recovery_actions(recovery_actions)
    support_bundle = support_bundle_summary(paths)
    if status != "ready":
        next_steps.append(f"Generate a sanitized support bundle: `{support_bundle['command']}`.")
    summary: dict[str, object] = {
        "status": status,
        "server": "running" if reachable else "stopped",
        "auth": "configured" if config.auth_token else "missing",
        "pairing": pairing,
        "engine_runtime": _engine_runtime_summary(doctor_results),
        "installed_voice_count": voice_count,
        "storage": {
            "writable": storage_writable,
            "used_bytes": storage["used_bytes"],
            "available_bytes": available_bytes,
        },
        "catalog": _check_status(doctor_results, "catalog_available"),
        "baseline_install": bundled_baseline_install_metadata(),
        "language_support": language_support_summary(),
        "release_guidance": release_guidance().to_json(),
        "runtime_policy": appliance_runtime_policy(),
        "doctor": doctor_results,
        "recovery_actions": tuple(recovery_actions),
        "support_bundle": support_bundle,
        "next_steps": tuple(dict.fromkeys(next_steps)),
        "developer_detail_available": True,
    }
    summary["capability_readiness"] = build_capability_readiness_manifest(summary)
    return summary


def support_bundle_summary(paths: RuntimePaths) -> dict[str, object]:
    _ = paths
    return {
        "bundle_type": "diagnostics_export",
        "command": "mery launch --action support-bundle --json",
        "default_output": "diagnostics/support-bundle.json",
        "local_only": True,
        "offline": True,
        "safe_to_review_before_sharing": True,
        "excludes": (
            "raw input text",
            "tokens and API keys",
            "pairing codes",
            "reference audio and audio payloads",
            "private filesystem paths and URLs",
            "model binaries",
        ),
    }


def write_support_bundle(paths: RuntimePaths) -> dict[str, object]:
    summary = support_bundle_summary(paths)
    relative_output = "diagnostics/support-bundle.json"
    output_path = paths.base_dir / relative_output
    payload = DiagnosticsExportBuilder(data_dir=paths.base_dir).build()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return {
        **summary,
        "written": True,
        "output": relative_output,
        "schema_version": payload["schema_version"],
        "sections": tuple(
            key for key in payload if key not in {"schema_version", "bundle_type", "generated_at"}
        ),
    }


def _readiness_recovery_actions(
    *,
    reachable: bool,
    auth_configured: bool,
    voice_count: int,
    storage_writable: bool | None,
    doctor_results: list[dict[str, str | None]],
) -> list[dict[str, str]]:
    blockers: list[tuple[ReadinessBlocker, str | None]] = []
    if not reachable:
        blockers.append((ReadinessBlocker.PORT_UNAVAILABLE, None))
    if not auth_configured:
        blockers.append((ReadinessBlocker.AUTH_PAIRING_REQUIRED, None))
    if voice_count == 0:
        blockers.append((ReadinessBlocker.NO_INSTALLED_VOICE, None))
    if storage_writable is False:
        blockers.append((ReadinessBlocker.STORAGE_NOT_WRITABLE, None))

    for result in doctor_results:
        status = result.get("status")
        if status not in {"fail", "warn"}:
            continue
        check = str(result.get("check") or "")
        detail = result.get("detail")
        if check in {"engine_availability", "engine_health"}:
            blockers.append((ReadinessBlocker.MISSING_PROVIDER_RUNTIME, detail))
        elif check == "model_availability":
            blockers.append((ReadinessBlocker.NO_INSTALLED_VOICE, detail))
        elif check == "token_configured":
            blockers.append((ReadinessBlocker.AUTH_PAIRING_REQUIRED, detail))
        elif check in {"disk_space", "platform_paths"}:
            blockers.append((ReadinessBlocker.STORAGE_NOT_WRITABLE, detail))
        elif check == "catalog_available":
            blockers.append((ReadinessBlocker.CATALOG_PROBLEM, detail))

    actions: list[dict[str, str]] = []
    seen: set[ReadinessBlocker] = set()
    for blocker, detail in blockers:
        if blocker in seen:
            continue
        seen.add(blocker)
        actions.append(recovery_action_for(blocker, detail=detail).to_json())
    return actions


def _next_steps_for_recovery_actions(actions: list[dict[str, str]]) -> list[str]:
    steps: list[str] = []
    for action in actions:
        command = action.get("command")
        if command:
            steps.append(f"{action['title']}: `{command}`.")
        else:
            steps.append(action["title"])
    return steps


def _check_status(results: list[dict[str, str | None]], check: str) -> str:
    for result in results:
        if result["check"] == check:
            return str(result["status"])
    return "unknown"


def _engine_runtime_summary(results: list[dict[str, str | None]]) -> str:
    status = _check_status(results, "engine_availability")
    if status == "ok":
        return "available"
    if status == "warn":
        return "degraded"
    if status == "fail":
        return "unavailable"
    return "unknown"


def language_support_summary() -> dict[str, object]:
    catalog = load_bundled_catalog()
    catalog_locales = sorted(
        {
            locale
            for model in catalog.models
            for locale in (model.supported_locales or [model.locale])
        }
    )
    return {
        "scope": "installed_or_catalog_voice",
        "catalog_locales": catalog_locales,
        "p1_audio_gate_locale": "en-US",
        "p1_audio_gate_voice": "piper-plus.en-us.lessac-low",
        "wording": (
            "Language support is model-dependent; choose an installed or catalog voice "
            "whose BCP-47 locale matches the text."
        ),
    }


def pairing_status(paths: RuntimePaths) -> dict[str, object]:
    config_path = paths.config_dir / "config.json"
    if not config_path.exists():
        return {
            "paired": False,
            "auth": "missing",
            "token_present": False,
            "setup_url": setup_url(load_config(paths)),
            "recovery_action": recovery_action_for(
                ReadinessBlocker.AUTH_PAIRING_REQUIRED
            ).to_json(),
        }
    config = load_config(paths)
    token_present = bool(config.auth_token)
    return {
        "paired": token_present,
        "auth": "configured" if token_present else "missing",
        "token_present": token_present,
        "setup_url": setup_url(config),
        "recovery_action": None
        if token_present
        else recovery_action_for(ReadinessBlocker.AUTH_PAIRING_REQUIRED).to_json(),
    }


def create_pairing_challenge(paths: RuntimePaths) -> dict[str, object]:
    store = HelperConfigStore(paths.config_dir)
    config = store.load_or_create()
    challenge = PairingService(config_store=store, config=config).create_challenge()
    return {
        "pairing_code": challenge.code,
        "setup_url": challenge.setup_url,
        "expires_at": challenge.expires_at.isoformat(),
        "expires_in_seconds": 600,
        "token_disclosed": False,
        "claim_endpoint": "/v1/pair/claim",
        "guidance": (
            "Enter this one-time code in your client; "
            "the long-lived token is never printed by the launcher."
        ),
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
    if not is_port_available(config.port):
        raise OSError(f"port {config.port} is unavailable on 127.0.0.1")
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
