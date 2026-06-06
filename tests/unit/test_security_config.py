import json
import stat
import uuid
from pathlib import Path

import pytest

from mery_tts.security import config as security_config
from mery_tts.security.config import HelperConfig, HelperConfigStore


def test_first_run_creates_stable_helper_id_and_token(tmp_path: Path) -> None:
    store = HelperConfigStore(tmp_path)

    created = store.load_or_create()
    loaded = store.load_or_create()

    assert created.helper_id == loaded.helper_id
    assert created.auth_token == loaded.auth_token
    assert len(created.auth_token) >= 32


def test_first_run_uses_uuid_and_secrets_for_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        security_config.uuid,
        "uuid4",
        lambda: uuid.UUID("12345678-1234-5678-1234-567812345678"),
    )
    monkeypatch.setattr(security_config.secrets, "token_urlsafe", lambda size: f"token-{size}-" * 6)

    created = HelperConfigStore(tmp_path).load_or_create()

    assert created.helper_id == "mery-12345678123456781234567812345678"
    assert created.auth_token == "token-32-" * 6


def test_config_file_uses_owner_only_permissions_where_supported(tmp_path: Path) -> None:
    store = HelperConfigStore(tmp_path)
    store.load_or_create()

    mode = stat.S_IMODE(store.config_path.stat().st_mode)

    assert mode & stat.S_IRWXG == 0
    assert mode & stat.S_IRWXO == 0


def test_port_defaults_env_override_and_bound_port_recording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    default_config = HelperConfigStore(tmp_path / "default").load_or_create()

    monkeypatch.setenv("MERY_TTS_PORT", "9876")
    store = HelperConfigStore(tmp_path / "override")
    config = store.load_or_create()
    updated = store.record_bound_port(9888)

    assert default_config.port == 8765
    assert config.port == 9876
    assert updated.bound_port == 9888
    assert json.loads(store.config_path.read_text())["bound_port"] == 9888


def test_token_rotation_invalidates_previous_token(tmp_path: Path) -> None:
    store = HelperConfigStore(tmp_path)
    original = store.load_or_create()

    rotated = store.rotate_token()

    assert rotated.helper_id == original.helper_id
    assert rotated.auth_token != original.auth_token
    assert store.load_or_create().auth_token == rotated.auth_token


def test_config_write_preserves_previous_config_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = HelperConfigStore(tmp_path)
    original = store.load_or_create()
    replacement = HelperConfig(
        helper_id=original.helper_id,
        auth_token="new-token" * 8,
        port=original.port,
    )

    def fail_replace(target: Path, source: Path) -> None:
        _ = target
        _ = source
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        store._write(replacement)

    assert store.load_or_create() == original
