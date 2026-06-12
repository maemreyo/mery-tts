import asyncio
import contextlib
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
from mery_tts.catalog.bundled import load_bundled_catalog
from mery_tts.diagnostics.doctor import (
    BackendStateCheck,
    CatalogAvailableCheck,
    DiskSpaceCheck,
    DoctorCheck,
    DoctorEngine,
    EngineAvailabilityCheck,
    EngineHealthCheck,
    ModelAvailabilityCheck,
    PlatformPathsCheck,
    ServerReachabilityCheck,
    TokenConfiguredCheck,
)
from mery_tts.diagnostics.export import DiagnosticsExportBuilder
from mery_tts.diagnostics.history import DiagnosticsEventStore
from mery_tts.engines.base import PCMChunk
from mery_tts.engines.discovery import discover_engine_registry
from mery_tts.hardware import HardwareBackendConfig
from mery_tts.help import get_help_topic, list_help_topics
from mery_tts.jobs import BundledInstallWorker, FileInstallJobStore, InstallJobService
from mery_tts.models.store import ModelStore
from mery_tts.security.config import HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.storage.identity import StorageIdentityStore

app = typer.Typer(no_args_is_help=True, help="Mery local TTS helper CLI.")
storage_app = typer.Typer(help="Manage Mery storage.")
app.add_typer(storage_app, name="storage")
models_app = typer.Typer(help="Manage Mery models.")
app.add_typer(models_app, name="models")
setup_app = typer.Typer(help="Mery setup and voice pack management.")
app.add_typer(setup_app, name="setup")
voice_packs_app = typer.Typer(help="Manage voice packs.")
app.add_typer(voice_packs_app, name="voice-packs")


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


@app.command("help-topic")
def help_topic(
    topic_id: str | None = typer.Argument(
        None,
        help="Local offline help topic ID. Omit to list available topics.",
    ),
) -> None:
    if topic_id is None:
        typer.echo("topic_id | title")
        for topic in list_help_topics():
            typer.echo(f"{topic.topic_id} | {topic.title}")
        return

    try:
        topic = get_help_topic(topic_id)
    except KeyError as exc:
        typer.echo(f"unknown help topic: {topic_id}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(topic.body)


@app.command()
def doctor(
    deep: bool = typer.Option(False, "--deep", help="Run real synthesis smoke tests."),
    providers: str = typer.Option(
        "", "--providers", help="Comma-separated provider list for smoke (e.g. piper-plus,kokoro)."
    ),
) -> None:
    paths = _runtime_paths()
    config_store = HelperConfigStore(paths.config_dir)
    config = config_store.load_or_create()

    engine_registry = discover_engine_registry()
    valid_engine_ids = set(engine_registry.adapters.keys())

    model_store = ModelStore(paths.models_dir / "artifacts")
    installed_models = [
        m.model_id for m in model_store.list_installed() if m.engine_id in valid_engine_ids
    ]

    checks: list[DoctorCheck] = [
        EngineAvailabilityCheck(engine_registry=engine_registry),
        EngineHealthCheck(unhealthy=[]),
        BackendStateCheck(config=HardwareBackendConfig(default_backend="auto")),
        ModelAvailabilityCheck(installed_models=installed_models),
        TokenConfiguredCheck(config_path=paths.config_dir / "config.json"),
        ServerReachabilityCheck(port=config.port),
        DiskSpaceCheck(models_dir=paths.models_dir),
        PlatformPathsCheck(writable_dirs=[paths.base_dir, paths.config_dir, paths.models_dir]),
        CatalogAvailableCheck(),
    ]

    engine = DoctorEngine(checks=checks, data_dir=paths.base_dir)
    results = engine.run()
    typer.echo("check | status | detail")
    for result in results:
        typer.echo(f"{result.check} | {result.status} | {result.detail}")

    if deep:
        typer.echo("\n--- Deep smoke ---")
        provider_list = [p.strip() for p in providers.split(",") if p.strip()] or [
            "piper-plus",
            "kokoro",
        ]
        _run_deep_smoke(paths, provider_list)

    raise typer.Exit(engine.exit_code(results))


def _run_deep_smoke(paths: "RuntimePaths", providers: list[str]) -> None:
    """Run deep smoke tests through the synthesis service."""
    import asyncio

    from mery_tts.engines.discovery import discover_engine_registry
    from mery_tts.smoke.record import SmokeRecordStore
    from mery_tts.smoke.service import SmokeService
    from mery_tts.synthesis import SpeechSynthesisService
    from mery_tts.voice import VoiceRegistry

    registry = discover_engine_registry()
    voice_registry = VoiceRegistry(registry.adapters)
    store = StorageIdentityStore(paths.models_dir)
    descriptors = store.hydrate_installed_voice_descriptors()
    for desc in descriptors:
        with contextlib.suppress(ValueError, KeyError):
            voice_registry.register(desc)

    synthesis_service = SpeechSynthesisService(
        voice_registry=voice_registry,
        purpose="smoke",
    )
    smoke_store = SmokeRecordStore(data_dir=paths.base_dir)
    smoke_service = SmokeService(
        synthesis_service=synthesis_service,
        record_store=smoke_store,
    )
    results = asyncio.run(smoke_service.smoke_providers(providers=providers))
    for result in results:
        status_detail = ""
        if result.sample_rate_hz is not None:
            status_detail = f" ({result.sample_rate_hz}Hz, {result.channels}ch)"
        if result.failure_detail:
            status_detail = f" — {result.failure_detail}"
        typer.echo(f"smoke | {result.voice_id} | {result.status.value}{status_detail}")


@app.command("diagnostics-history")
def diagnostics_history(
    delete: bool = typer.Option(False, "--delete", help="Delete local diagnostics history."),
) -> None:
    store = DiagnosticsEventStore(data_dir=_runtime_paths().base_dir)
    if delete:
        typer.echo(f"diagnostics.history_deleted: {store.clear()}")
        return
    status = store.retention_status()
    typer.echo(
        "diagnostics.history: "
        f"event_count={status['event_count']} "
        f"retention_days={status['retention_days']} "
        f"max_events={status['max_events']} "
        f"storage_corrupted={str(status['storage_corrupted']).lower()}"
    )


@app.command("diagnostics-export")
def diagnostics_export(
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write export bundle to a JSON file instead of stdout.",
        ),
    ] = None,
) -> None:
    paths = _runtime_paths()
    payload = DiagnosticsExportBuilder(data_dir=paths.base_dir).build()
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is None:
        typer.echo(serialized, nl=False)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized)
    typer.echo(f"diagnostics.export_written: {output}")


@app.command()
def launch(
    list_actions: bool = typer.Option(False, "--list-actions", help="List launcher actions."),
    action: str | None = typer.Option(None, "--action", help="Run a launcher action by ID."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    yes: bool = typer.Option(False, "--yes", help="Approve confirmation-gated actions."),
) -> None:
    """Open the interactive Mery launcher."""
    from mery_tts.cli.launcher import run_launcher

    exit_code = run_launcher(
        list_actions=list_actions,
        action=action,
        json_output=json_output,
        yes=yes,
    )
    raise typer.Exit(exit_code)


@app.command()
def smoke(
    providers: str = typer.Option(
        "piper-plus,kokoro",
        "--providers",
        help="Comma-separated provider list for smoke.",
    ),
) -> None:
    """Run provider-specific smoke checks through real synthesis."""
    paths = _runtime_paths()
    provider_list = [p.strip() for p in providers.split(",") if p.strip()]
    _run_deep_smoke(paths, provider_list)


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
    store = StorageIdentityStore(paths.models_dir)
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


@models_app.command("list")
def models_list() -> None:
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


@models_app.command("install")
def models_install(
    model_id: str = typer.Argument(..., help="Model ID to install (e.g. piper-plus.vi-vn.demo)"),
) -> None:
    paths = _runtime_paths()
    model_store = ModelStore(paths.models_dir)
    storage_store = StorageIdentityStore(paths.models_dir)

    def refresh() -> None:
        pass

    job_service = InstallJobService(
        store=storage_store,
        refresh=refresh,
        job_store=FileInstallJobStore(model_store.root_path / "jobs" / "install"),
    )

    worker = BundledInstallWorker(
        job_service=job_service,
        artifacts_dir=paths.models_dir / "artifacts",
        catalog=load_bundled_catalog(),
    )

    engine_id = "piper-plus" if "piper" in model_id.lower() else "kokoro"
    job = job_service.start_install(
        catalog_entry_id=model_id,
        voice_id=model_id,
        engine_id=engine_id,
        artifact_id=model_id,
    )

    typer.echo(f"Starting install job {job.job_id} for {model_id}...")
    result = asyncio.run(worker.execute(job.job_id))
    typer.echo(f"Status: {result.status.value}")
    if result.error:
        typer.echo(f"Error: {result.error}")
        raise typer.Exit(1)


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


def _remove_directory_contents(path: Path) -> int:
    removed = 0
    if not path.exists():
        return removed
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    return removed


@storage_app.command("cleanup")
def storage_cleanup(
    target: str = typer.Option(..., "--target", help="cache, logs, or diagnostics"),
) -> None:
    paths = _runtime_paths()
    cleanup_targets = {
        "cache": paths.cache_dir,
        "logs": paths.logs_dir,
        "diagnostics": paths.base_dir / "diagnostics",
    }
    if target == "models":
        typer.echo("storage.cleanup_refused: model cleanup is not supported; models_protected=true")
        raise typer.Exit(1)
    if target not in cleanup_targets:
        typer.echo("storage.cleanup_failed: target must be cache, logs, or diagnostics")
        raise typer.Exit(2)

    removed = _remove_directory_contents(cleanup_targets[target])
    typer.echo(
        f"storage.cleanup_complete: target={target}; removed={removed}; models_protected=true"
    )


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


@setup_app.command("recommend")
def setup_recommend(
    client: str = typer.Option("mery-cli", "--client", help="Client identity."),
    intent: str = typer.Option("general", "--intent", help="Use-case intent."),
    locale: str = typer.Option("", "--locale", help="Locale preference."),
) -> None:
    from mery_tts.catalog.voice_pack import VoicePackGraph
    from mery_tts.setup.services import (
        SetupService,
        SimpleInstalledRuntimeStore,
        SimpleInstalledVoiceStore,
        SimpleVoicePackCatalog,
    )

    paths = _runtime_paths()
    store = StorageIdentityStore(paths.models_dir)
    descriptors = store.hydrate_installed_voice_descriptors()
    installed_ids = {d.voice_id for d in descriptors}

    catalog = SimpleVoicePackCatalog(VoicePackGraph())
    service = SetupService(
        catalog=catalog,
        installed_voices=SimpleInstalledVoiceStore(installed_ids),
        installed_runtimes=SimpleInstalledRuntimeStore(),
    )
    recommendations = service.recommend(
        client=client,
        intent=intent,
        locale=locale or None,
    )
    result = [
        {
            "voice_pack_id": r.voice_pack_id,
            "display_name": r.display_name,
            "status": r.status,
            "reason": r.reason,
        }
        for r in recommendations
    ]
    typer.echo(json.dumps({"recommendations": result, "client": client, "intent": intent}))


@setup_app.command("url")
def setup_url(
    client: str = typer.Option("mery-cli", "--client", help="Client identity."),
    intent: str = typer.Option("general", "--intent", help="Use-case intent."),
    locale: str = typer.Option("", "--locale", help="Locale preference."),
) -> None:
    from mery_tts.setup.intent import SetupIntent

    si = SetupIntent(
        client=client,
        intent=intent,
        locale=locale or None,
    )
    typer.echo(si.to_console_url())


@voice_packs_app.command("list")
def voice_packs_list() -> None:
    from mery_tts.catalog.bundled import load_bundled_catalog
    from mery_tts.catalog.bundled_voice_pack import bundled_catalog_to_voice_pack_graph
    from mery_tts.catalog.voice_pack import voice_packs_for_catalog_graph

    paths = _runtime_paths()
    store = StorageIdentityStore(paths.models_dir)
    descriptors = store.hydrate_installed_voice_descriptors()
    installed_ids = {d.voice_id for d in descriptors}

    graph = bundled_catalog_to_voice_pack_graph(load_bundled_catalog())
    packs = voice_packs_for_catalog_graph(
        voice_pack_graph=graph,
        installed_voice_ids=installed_ids,
        installed_runtime_ids=set(),
    )
    typer.echo(json.dumps({"voice_packs": packs}))


@voice_packs_app.command("install")
def voice_packs_install(
    pack_id: str = typer.Argument(..., help="Voice pack ID to install."),
) -> None:
    asyncio.run(_do_voice_pack_install(pack_id))


async def _do_voice_pack_install(pack_id: str) -> None:
    from mery_tts.catalog.bundled import load_bundled_catalog
    from mery_tts.catalog.bundled_voice_pack import bundled_catalog_to_voice_pack_graph
    from mery_tts.catalog.graph_adapter import legacy_catalog_to_graph
    from mery_tts.jobs.install import JobStatus
    from mery_tts.setup.plan import InstallPlanError, InstallPlanStepKind, resolve_install_plan

    paths = _runtime_paths()
    catalog = load_bundled_catalog()
    catalog_graph = legacy_catalog_to_graph(catalog)
    voice_pack_graph = bundled_catalog_to_voice_pack_graph(catalog)

    store = StorageIdentityStore(paths.models_dir)
    descriptors = store.hydrate_installed_voice_descriptors()
    installed_ids = {d.voice_id for d in descriptors}

    try:
        plan = resolve_install_plan(
            voice_pack_id=pack_id,
            voice_pack_graph=voice_pack_graph,
            catalog_graph=catalog_graph,
            installed_voice_ids=installed_ids,
        )
    except InstallPlanError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from exc

    if plan.is_empty:
        typer.echo("Already installed.")
        return

    artifacts_dir = paths.base_dir / "models" / "artifacts"
    job_service = InstallJobService(store=store, refresh=lambda: None)
    worker = BundledInstallWorker(
        job_service=job_service,
        catalog=catalog,
        catalog_graph=catalog_graph,
        artifacts_dir=artifacts_dir,
    )

    voice_steps = [s for s in plan.steps if s.kind == InstallPlanStepKind.WRITE_VOICE_MANIFEST]
    for step in voice_steps:
        artifact_id = step.artifact_id or step.target_id
        engine_id = step.engine_id or "piper-plus"
        typer.echo(f"Downloading {artifact_id}…", nl=False)
        job = job_service.start_install(
            catalog_entry_id=artifact_id,
            voice_id=step.target_id,
            engine_id=engine_id,
            artifact_id=artifact_id,
        )
        result = await worker.execute(job.job_id)
        if result.status == JobStatus.FAILED:
            typer.echo(f" failed\nerror: {result.error}", err=True)
            raise typer.Exit(1)
        typer.echo(" done")

    typer.echo(f"Voice pack {pack_id!r} installed.")


if __name__ == "__main__":
    app()
