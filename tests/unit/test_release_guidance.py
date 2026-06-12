from __future__ import annotations

from pathlib import Path

from mery_tts.release import detect_install_method, release_guidance


def test_detect_install_method_identifies_uv_tool_from_prefix(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    method = detect_install_method(
        executable=str(tmp_path / "uv" / "tools" / "mery-tts-server" / "bin" / "python"),
        prefix=str(tmp_path / "uv" / "tools" / "mery-tts-server"),
    )

    assert method == "uv_tool"


def test_detect_install_method_identifies_pipx_from_prefix(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    method = detect_install_method(
        executable=str(tmp_path / "pipx" / "venvs" / "mery-tts-server" / "bin" / "python"),
        prefix=str(tmp_path / "pipx" / "venvs" / "mery-tts-server"),
    )

    assert method == "pipx"


def test_detect_install_method_identifies_editable_checkout(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "src" / "mery_tts").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'mery-tts-server'\n")
    monkeypatch.chdir(tmp_path)

    assert detect_install_method(executable="/venv/bin/python", prefix="/venv") == "editable"


def test_detect_install_method_returns_unknown_without_fragile_path_assumption(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    assert (
        detect_install_method(executable="/opt/python/bin/python", prefix="/opt/python")
        == "unknown"
    )


def test_release_guidance_renders_package_manager_owned_commands() -> None:
    uv_guidance = release_guidance(install_method="uv_tool").to_json()
    pipx_guidance = release_guidance(install_method="pipx").to_json()
    editable_guidance = release_guidance(install_method="editable").to_json()
    unknown_guidance = release_guidance(install_method="unknown").to_json()

    assert uv_guidance["upgrade_command"] == "uv tool upgrade mery-tts-server"
    assert uv_guidance["runtime_repair_commands"]["piper-plus"] == (
        "uv tool install 'mery-tts-server[piper-plus]' --force"
    )
    assert pipx_guidance["upgrade_command"] == "pipx upgrade mery-tts-server"
    assert pipx_guidance["runtime_repair_commands"]["kokoro"] == (
        "pipx inject mery-tts-server kokoro-onnx onnxruntime --force"
    )
    assert editable_guidance["upgrade_command"] == "git pull && uv sync --all-extras"
    assert "uv tool upgrade" in unknown_guidance["upgrade_command"]
    assert unknown_guidance["confidence"] == "low"
    assert unknown_guidance["self_mutating_updater"] is False
    assert unknown_guidance["state_recovery_owned_by_mery"] is True
    assert unknown_guidance["stable_preview_nightly_deferred"] is True
    assert unknown_guidance["version_layers"] == {
        "app_version": "0.1.0",
        "api_major": "v1",
        "catalog_schema_version": "catalog-v1",
        "voice_pack_manifest_version": "voice-pack-v1",
        "provider_capability_version": "provider-capability-v1",
    }
