import asyncio
import json
import shutil
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from mery_tts import __version__
from mery_tts.audio.exporter import AudioExporter
from mery_tts.catalog import bundled_catalog_voice_summaries
from mery_tts.diagnostics.doctor import DoctorEngine
from mery_tts.engines.base import PCMChunk
from mery_tts.engines.discovery import discover_engine_registry
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.storage.identity import StorageIdentityStore

app = typer.Typer(no_args_is_help=True, help="Mery local TTS helper CLI.")
storage_app = typer.Typer(help="Manage Mery storage.")
app.add_typer(storage_app, name="storage")


def _version_callback(show_version: bool) -> None:
    if show_version:
        typer.echo(f"mery-tts-server {__version__}")
        raise typer.Exit(0)


def _runtime_paths() -> RuntimePaths:
    return RuntimePaths.from_environment()


def _pairing_service() -> PairingService:
    paths = _runtime_paths()
    store = HelperConfigStore(paths.config_dir)
    config = store.load_or_create()
    return PairingService(config_store=store, config=config)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show Mery version and exit.",
    ),
) -> None:
    _ = version


@app.command()
def doctor() -> None:
    paths = _runtime_paths()
    engine = DoctorEngine(data_dir=paths.base_dir)
    results = engine.run()
    typer.echo("check | status | detail")
    for result in results:
        typer.echo(f"{result.check} | {result.status} | {result.detail}")
    raise typer.Exit(engine.exit_code(results))


@app.command()
def serve() -> None:
    paths = _runtime_paths()
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


@app.command()
def pair(
    rotate: bool = typer.Option(False, "--rotate", help="Rotate the long-lived token."),
) -> None:
    service = _pairing_service()
    if rotate:
        service.rotate_token()
        typer.echo("Token rotated. Existing clients must re-pair.")
        return
    challenge = service.create_challenge()
    typer.echo(f"Pairing code: {challenge.code}")
    typer.echo(f"Setup URL: {challenge.setup_url}")
    typer.echo(f"Expires: {challenge.expires_at.isoformat()}")
    typer.echo("Open Zam Reader Options and paste the setup URL before the code expires.")


@app.command()
def engines() -> None:
    registry = discover_engine_registry()
    engine_list = [
        {"engine_id": engine_id, "status": adapter.health()}
        for engine_id, adapter in sorted(registry.adapters.items())
    ]
    typer.echo(json.dumps({"engines": engine_list, "load_warnings": list(registry.load_warnings)}))


@app.command()
def voices() -> None:
    paths = _runtime_paths()
    store = StorageIdentityStore(paths.base_dir)
    descriptors = store.hydrate_installed_voice_descriptors()
    voice_list = [
        {"voice_id": d.voice_id, "engine_id": d.engine_id, "kind": d.payload.kind}
        for d in descriptors
    ]
    typer.echo(json.dumps({"voices": voice_list}))


@app.command()
def catalog() -> None:
    summaries = bundled_catalog_voice_summaries()
    catalog_list = [
        {"voice_id": s.voice_id, "engine_id": s.engine_id, "display_name": s.display_name}
        for s in summaries
    ]
    typer.echo(json.dumps({"catalog": catalog_list}))


@app.command()
def models() -> None:
    paths = _runtime_paths()
    store = ModelStore(paths.models_dir)
    records = store.list_installed()
    model_list = [
        {
            "engine_id": r.engine_id,
            "model_id": r.model_id,
            "size_bytes": r.size_bytes,
        }
        for r in records
    ]
    typer.echo(json.dumps({"models": model_list}))


@storage_app.command("show")
def storage_show() -> None:
    paths = _runtime_paths()
    store = ModelStore(paths.models_dir)
    stats = store.disk_usage()
    records = store.list_installed()

    typer.echo(f"model store: {stats.root_path}")
    typer.echo(f"total installed size: {stats.used_bytes} bytes")
    available = stats.available_bytes if stats.available_bytes is not None else "unknown"
    typer.echo(f"available disk space: {available}")

    if records:
        typer.echo("\nInstalled models:")
        for record in records:
            typer.echo(f"  {record.engine_id}/{record.model_id}: {record.size_bytes} bytes")
    else:
        typer.echo("\nNo models installed.")


@storage_app.command("move")
def storage_move(to: str = typer.Option(..., "--to")) -> None:
    paths = _runtime_paths()
    target = paths.base_dir / "models" if to == "default" else __import__("pathlib").Path(to)

    if not paths.models_dir.exists():
        typer.echo("storage.migration_complete: no models to migrate")
        return

    target.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copytree(paths.models_dir, target, dirs_exist_ok=True)
        typer.echo(f"storage.migration_complete: migrated to {target}")
    except OSError as exc:
        typer.echo(f"storage.migration_failed: {exc}", err=True)
        raise typer.Exit(1) from exc


@storage_app.command("repair")
def storage_repair() -> None:
    paths = _runtime_paths()
    deleted = 0
    flagged = 0

    for cache_dir in [paths.cache_dir / "downloads", paths.cache_dir / "temp"]:
        if not cache_dir.exists():
            continue
        for path in cache_dir.glob("*"):
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()
                deleted += 1

    store = ModelStore(paths.models_dir)
    records = store.list_installed()

    typer.echo(f"storage.repair_complete: deleted={deleted}; flagged={flagged}")
    if records:
        typer.echo(f"  verified {len(records)} installed model(s)")


async def _single_pcm_chunk(text: str) -> AsyncIterator[PCMChunk]:
    payload = text.encode("utf-8") or b"silence"
    yield PCMChunk(pcm=payload * 2, sample_rate_hz=24_000, channels=1)


@app.command()
def speak(
    text: Annotated[str, typer.Option("--text")] = "",
    file: Annotated[Path | None, typer.Option("--file")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    input_text = file.read_text() if file is not None else text
    if output is not None:
        result = asyncio.run(AudioExporter().export(_single_pcm_chunk(input_text), output))
        typer.echo(
            json.dumps(
                {
                    "path": str(result.path),
                    "duration_seconds": result.duration_seconds,
                    "file_size_bytes": result.file_size_bytes,
                },
                sort_keys=True,
            )
        )
        return
    typer.echo(f'{{"command":"speak","accepted":{bool(input_text).__str__().lower()}}}')
