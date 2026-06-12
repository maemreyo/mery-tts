from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

BASELINE_MODEL_ID = "piper-plus.en-us.lessac-low"
BASELINE_PACK_ID = "pack.en-us"
DEFAULT_PORT = 9878
POLL_INTERVAL_SECONDS = 0.25
POLL_TIMEOUT_SECONDS = 180.0
DRY_RUN_TIMESTAMP = "1970-01-01T00:00:00+00:00"


@dataclass(frozen=True, slots=True)
class RealVoiceSmokeConfig:
    repo_root: Path
    artifact_dir: Path
    dry_run: bool = False
    keep_temp: bool = False
    port: int = DEFAULT_PORT
    python_executable: str = sys.executable


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _replace_placeholders(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, str):
        result = value
        for real, placeholder in sorted(
            replacements.items(), key=lambda item: len(item[0]), reverse=True
        ):
            result = result.replace(real, placeholder)
        return result
    if isinstance(value, list):
        return [_replace_placeholders(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_placeholders(item, replacements) for key, item in value.items()}
    return value


def _run_command(
    name: str,
    argv: tuple[str, ...],
    *,
    cwd: Path,
    env: dict[str, str],
    dry_run: bool,
    timeout: int = 120,
) -> dict[str, object]:
    started_at = _now()
    if dry_run:
        return {
            "name": name,
            "argv": list(argv),
            "returncode": 0,
            "stdout": "dry-run " + " ".join(argv),
            "stderr": "",
            "started_at": DRY_RUN_TIMESTAMP,
            "finished_at": DRY_RUN_TIMESTAMP,
            "dry_run": True,
        }
    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    return {
        "name": name,
        "argv": list(argv),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "started_at": started_at,
        "finished_at": _now(),
        "dry_run": False,
    }


def _doctor_preflight_ok(result: dict[str, object]) -> bool:
    returncode = result.get("returncode")
    output = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    return returncode in {0, 2} and "Traceback" not in output


def _json_from_command(result: dict[str, object]) -> dict[str, Any]:
    if result["returncode"] != 0:
        raise RuntimeError(f"{result['name']} failed with exit code {result['returncode']}")
    payload = json.loads(str(result.get("stdout") or "{}"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{result['name']} did not return a JSON object")
    return cast("dict[str, Any]", payload)


def _assert_local_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("real voice smoke only calls local HTTP endpoints")


def _request_json(
    method: str,
    url: str,
    *,
    token: str,
    payload: dict[str, object] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    _assert_local_http_url(url)
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        payload_data = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload_data, dict):
        raise RuntimeError(f"{url} did not return a JSON object")
    return cast("dict[str, Any]", payload_data)


def _request_bytes(
    method: str,
    url: str,
    *,
    token: str,
    payload: dict[str, object],
    timeout: float = 60.0,
) -> dict[str, object]:
    _assert_local_http_url(url)
    request = urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps(payload).encode("utf-8"),
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            body = bytes(response.read())
            return {
                "status": response.status,
                "content_type": response.headers.get("Content-Type", ""),
                "byte_count": len(body),
            }
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{method} {url} failed with HTTP {exc.code}: {error_body}"
        ) from exc


def _request_json_error(
    method: str,
    url: str,
    *,
    token: str,
    payload: dict[str, object],
    timeout: float = 30.0,
) -> dict[str, object]:
    _assert_local_http_url(url)
    request = urllib.request.Request(  # noqa: S310
        url,
        data=json.dumps(payload).encode("utf-8"),
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return {
                "status": response.status,
                "content_type": response.headers.get("Content-Type", ""),
                "body": json.loads(response.read().decode("utf-8")),
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "content_type": exc.headers.get("Content-Type", ""),
            "body": json.loads(exc.read().decode("utf-8")),
        }


def _wait_for_server(base_url: str, *, token: str) -> dict[str, Any]:
    deadline = time.monotonic() + 30.0
    last_error = "server not reached"
    while time.monotonic() < deadline:
        try:
            return _request_json("GET", f"{base_url}/v1/health", token=token, timeout=2.0)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            time.sleep(0.25)
    raise RuntimeError(last_error)


def _poll_job(base_url: str, *, token: str, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    status: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status = _request_json("GET", f"{base_url}/v1/models/install/{job_id}", token=token)
        if status.get("status") in {"completed", "failed"}:
            return status
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"install job {job_id} did not finish; last status={status}")


def _load_token(data_dir: Path) -> str:
    config_path = data_dir / "config" / "config.json"
    config = json.loads(config_path.read_text())
    token = str(config["auth_token"])
    if not token:
        raise RuntimeError("generated auth token is empty")
    return token


def _dry_run_payload(
    config: RealVoiceSmokeConfig, temp_dir: Path, data_dir: Path
) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "harness": "piper-real-voice-readiness-smoke",
        "generated_at": DRY_RUN_TIMESTAMP,
        "dry_run": True,
        "repo_root": "<repo-root>",
        "artifact_dir": "<artifact-dir>",
        "temp_dir": "<temp-dir>",
        "data_dir": "<data-dir>",
        "baseline": {
            "pack_id": BASELINE_PACK_ID,
            "model_id": BASELINE_MODEL_ID,
            "provider": "piper-plus",
            "locale": "en-US",
        },
        "steps": [
            {"name": "isolated-storage", "status": "planned"},
            {"name": "explicit-confirmation", "status": "planned"},
            {"name": "durable-install-job", "status": "planned"},
            {"name": "installed-voice-status", "status": "planned"},
            {"name": "model-status", "status": "planned"},
            {"name": "openai-non-streaming-speech", "status": "planned"},
            {"name": "openai-uninstalled-voice-failure", "status": "planned"},
            {"name": "delete-cleanup", "status": "planned"},
        ],
        "openai_packaged_speech": {
            "endpoint": "/v1/audio/speech",
            "mode": "non_streaming",
            "streaming_secondary_for_p1": True,
            "success_request": {
                "model": "tts-1",
                "voice": BASELINE_MODEL_ID,
                "input": "<fixed-smoke-text>",
                "response_format": "pcm",
            },
            "expected_success": {
                "status": 200,
                "content_type_prefix": "audio/",
                "non_empty_audio": True,
            },
            "failure_request": {
                "model": "tts-1",
                "voice": "piper-plus.en-us.uninstalled-smoke",
                "input": "<fixed-smoke-text>",
                "response_format": "pcm",
            },
            "expected_failure": {
                "structured_json_error": True,
                "no_audio_bytes": True,
            },
            "secret_redaction": {
                "authorization_header": "<redacted>",
                "token_recorded": False,
            },
        },
    }


def run_smoke(config: RealVoiceSmokeConfig) -> Path:
    config.artifact_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="mery-real-voice-smoke-"))
    data_dir = temp_dir / "data"
    env = os.environ.copy()
    env["MERY_TTS_DATA_DIR"] = str(data_dir)
    env["MERY_TTS_PORT"] = str(config.port)

    output_path = config.artifact_dir / "piper-real-voice-smoke-result.json"
    server: subprocess.Popen[str] | None = None
    commands: list[dict[str, object]] = []
    api_artifacts: dict[str, object] = {}
    audio_bytes = 0
    try:
        if config.dry_run:
            output_path.write_text(
                json.dumps(
                    _dry_run_payload(config, temp_dir, data_dir),
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return output_path

        doctor = _run_command(
            "doctor",
            (config.python_executable, "-m", "mery_tts.cli.main", "doctor"),
            cwd=config.repo_root,
            env=env,
            dry_run=False,
        )
        commands.append(doctor)
        if not _doctor_preflight_ok(doctor):
            raise RuntimeError("doctor failed before real voice smoke")

        install_preview = _run_command(
            "install-baseline-preview",
            (
                config.python_executable,
                "-m",
                "mery_tts.cli.main",
                "launch",
                "--action",
                "install-baseline-voice",
                "--json",
            ),
            cwd=config.repo_root,
            env=env,
            dry_run=False,
        )
        commands.append(install_preview)
        preview_payload = _json_from_command(install_preview)
        if preview_payload.get("data", {}).get("job_started") is not False:
            raise RuntimeError("unconfirmed install unexpectedly started a job")

        server = subprocess.Popen(  # noqa: S603
            (
                config.python_executable,
                "-m",
                "mery_tts.cli.main",
                "serve",
            ),
            cwd=config.repo_root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        token = _load_token(data_dir)
        base_url = f"http://127.0.0.1:{config.port}"
        api_artifacts["health"] = _wait_for_server(base_url, token=token)
        confirmed_payload = _request_json(
            "POST",
            f"{base_url}/v1/models/install",
            token=token,
            payload={
                "schema_version": "v1",
                "request_id": "piper-real-voice-smoke-install",
                "model_id": BASELINE_MODEL_ID,
                "user_confirmed": True,
            },
        )
        api_artifacts["model_install"] = confirmed_payload
        job_id = str(confirmed_payload.get("job_id") or "")
        if not job_id:
            raise RuntimeError("confirmed API install did not return a job id")
        install_job = _poll_job(base_url, token=token, job_id=job_id)
        api_artifacts["install_job"] = install_job
        if install_job.get("status") != "completed":
            raise RuntimeError(f"install job did not complete: {install_job}")

        api_artifacts["installed_voices"] = _request_json(
            "GET", f"{base_url}/v1/voices/installed", token=token
        )
        api_artifacts["model_status_after_install"] = _request_json(
            "GET", f"{base_url}/v1/models/{BASELINE_MODEL_ID}", token=token
        )
        openai_success_request: dict[str, object] = {
            "model": "tts-1",
            "voice": BASELINE_MODEL_ID,
            "input": "Mery real voice readiness smoke.",
            "response_format": "pcm",
        }
        openai_success = _request_bytes(
            "POST",
            f"{base_url}/v1/audio/speech",
            token=token,
            payload=openai_success_request,
        )
        audio_bytes = cast("int", openai_success["byte_count"])
        content_type = str(openai_success["content_type"])
        status = cast("int", openai_success["status"])
        if status != 200:
            raise RuntimeError(f"OpenAI speech returned status {status}")
        if not content_type.startswith("audio/"):
            raise RuntimeError(f"OpenAI speech returned non-audio content type {content_type!r}")
        if audio_bytes <= 0:
            raise RuntimeError("OpenAI speech returned empty audio")

        openai_failure_request: dict[str, object] = {
            "model": "tts-1",
            "voice": "piper-plus.en-us.uninstalled-smoke",
            "input": "Mery real voice readiness smoke.",
            "response_format": "pcm",
        }
        openai_failure = _request_json_error(
            "POST",
            f"{base_url}/v1/audio/speech",
            token=token,
            payload=openai_failure_request,
        )
        failure_status = cast("int", openai_failure["status"])
        if failure_status < 400:
            raise RuntimeError("uninstalled voice unexpectedly produced partial success")
        if not str(openai_failure["content_type"]).startswith("application/json"):
            raise RuntimeError("uninstalled voice failure was not structured JSON")

        api_artifacts["openai_packaged_speech"] = {
            "endpoint": "/v1/audio/speech",
            "mode": "non_streaming",
            "streaming_secondary_for_p1": True,
            "success_request": {
                **openai_success_request,
                "input": "<fixed-smoke-text>",
            },
            "success_response": openai_success,
            "failure_request": {
                **openai_failure_request,
                "input": "<fixed-smoke-text>",
            },
            "failure_response": openai_failure,
            "secret_redaction": {
                "authorization_header": "<redacted>",
                "token_recorded": False,
            },
        }

        api_artifacts["delete"] = _request_json(
            "DELETE", f"{base_url}/v1/models/{BASELINE_MODEL_ID}", token=token
        )
        api_artifacts["model_status_after_delete"] = _request_json(
            "GET", f"{base_url}/v1/models/{BASELINE_MODEL_ID}", token=token
        )

        payload = {
            "schema_version": "v1",
            "harness": "piper-real-voice-readiness-smoke",
            "generated_at": _now(),
            "dry_run": False,
            "repo_root": str(config.repo_root),
            "artifact_dir": str(config.artifact_dir),
            "temp_dir": str(temp_dir),
            "data_dir": str(data_dir),
            "baseline": {
                "pack_id": BASELINE_PACK_ID,
                "model_id": BASELINE_MODEL_ID,
                "provider": "piper-plus",
                "locale": "en-US",
            },
            "commands": commands,
            "api_artifacts": api_artifacts,
            "audio_bytes": audio_bytes,
        }
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return output_path
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
        if not config.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run P1 Piper real voice readiness smoke.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path(".scratch/piper-real-voice-smoke"),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = RealVoiceSmokeConfig(
        repo_root=args.repo_root.resolve(),
        artifact_dir=args.artifact_dir.resolve(),
        dry_run=args.dry_run,
        keep_temp=args.keep_temp,
        port=args.port,
    )
    output_path = run_smoke(config)
    print(f"piper_real_voice_smoke_result={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
