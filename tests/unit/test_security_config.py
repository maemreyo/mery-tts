import json
import stat
from pathlib import Path

import pytest

from mery_tts.security.config import HelperConfigStore


def test_first_run_creates_stable_helper_id_and_token(tmp_path: Path) -> None:
    store = HelperConfigStore(tmp_path)

    created = store.load_or_create()
    loaded = store.load_or_create()

    assert created.helper_id == loaded.helper_id
    assert created.auth_token == loaded.auth_token
    assert len(created.auth_token) >= 32


def test_config_file_uses_owner_only_permissions_where_supported(tmp_path: Path) -> None:
    store = HelperConfigStore(tmp_path)
    store.load_or_create()

    mode = stat.S_IMODE(store.config_path.stat().st_mode)

    assert mode & stat.S_IRWXG == 0
    assert mode & stat.S_IRWXO == 0


def test_port_defaults_env_override_and_bound_port_recording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MERY_TTS_PORT", "9876")
    store = HelperConfigStore(tmp_path)

    config = store.load_or_create()
    updated = store.record_bound_port(9888)

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
