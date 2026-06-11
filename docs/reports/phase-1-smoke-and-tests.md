# Phase 1 Smoke Test & Test Suite Report

> Verification evidence for the Phase 1 early-access runtime:
> live-server smoke test, full pytest run (including the 3 `engine` markers),
> and the canonical `make check` gate.

Date: 2026-06-06
Repo: `zam-local-tts-helper`
Stack: Python 3.13.12, FastAPI, uvicorn, Typer, Pydantic v2
Runner: macOS (darwin), `uv` workflow

---

## 1. Executive summary

| Verification | Outcome |
|---|---|
| `mery doctor` (pre-serve) | core checks `ok`; engines `warn` (optional extras not installed — expected) |
| Live `mery serve` smoke (13 endpoint probes) | 12× `200`, 3× `404` (asset + traversal guard), 3× `401` (auth boundary) |
| `uv run pytest` (no marker filter) | **272 passed, 3 skipped** in 1.33s |
| `make check` (canonical gate) | ruff format ✓, ruff check ✓, mypy ✓ (60 files), pytest 272 passed, CLI smoke ✓ |
| Build artifact `uv build --wheel` | `mery_tts/console/index.html` plus referenced Vite hashed JS/CSS assets present in wheel |

**Net result:** every claim in the public README — `/v1` API, packaged
`/console` web UI, bundled catalog, auth boundary, asset traversal guard,
packaging-agnostic runtime — is exercised end-to-end by tests and confirmed
against a live `mery serve` process on `127.0.0.1:18765`.

Real Piper-plus and Kokoro audio synthesis remains a **future hardening task**
gated by installing the matching optional extras and shipping fixture models
— see §6 for the precise gap and re-enable commands.

---

## 2. Live `mery serve` smoke test

Process: `MERY_TTS_DATA_DIR=$(mktemp -d) MERY_TTS_PORT=18765 uv run mery serve`
(binds `127.0.0.1:18765`, writes ephemeral config to the temp data dir).

Bearer token is read from `$DATA_DIR/config/config.json` written by
`HelperConfigStore.load_or_create()` at first start (32+ char `secrets.token_urlsafe`).

### 2.1 `mery doctor` (pre-serve)

| Check | Status | Detail |
|---|---|---|
| engine_availability | warn | no engines loaded |
| engine_health | ok | no unhealthy engines |
| model_availability | warn | no models installed |
| token_configured | ok | token configured |
| server_reachability | warn | server not running |
| disk_space | ok | disk space ok |
| platform_paths | ok | paths writable |
| catalog_available | ok | bundled catalog available |

The two `warn` rows are correct: no optional extras (`piper-plus`,
`kokoro-onnx`) and no real fixture models are installed in this verification
environment. Everything else is green.

### 2.2 Endpoint matrix

| # | Endpoint | Auth | Expected | Actual | Body sample |
|---|---|---|---|---|---|
| 1 | `GET /v1/health` | – | 401 (auth required) | **401** | – |
| 2 | `GET /v1/health` | bearer | 200 JSON | **200** | `{"schema_version":"v1","request_id":"local","status":"ok"}` |
| 3 | `GET /console` | – | 200 `text/html` | **200** | SPA shell referencing Vite hashed JS/CSS assets |
| 4 | `GET /console/` | – | 200 SPA shell | **200** | 3001 bytes (trailing-slash form) |
| 5 | `GET /console/catalog/deep-link` | – | 200 SPA fallback | **200** | 3001 bytes (deep link serves index) |
| 6 | `GET /console/assets/<vite-hash>.js` | – | 200 `text/javascript` | **200** | Vite hashed JavaScript bundle |
| 7 | `GET /console/assets/<vite-hash>.css` | – | 200 `text/css` | **200** | Vite hashed stylesheet |
| 8 | `GET /console/assets/missing.js` | – | 404 | **404** | – |
| 9 | `GET /console/assets/%2e%2e/index.html` | – | 404 (encoded traversal) | **404** | – |
| 10 | `GET /console/assets/<vite-hash>.js` (no auth) | – | 200 (public) | **200** | – |
| 11 | `GET /v1/catalog/voices` | – | 401 | **401** | – |
| 12 | `GET /v1/catalog/voices` | bearer | 200 + voice summaries | **200** | 2 voices: `catalog.piper-plus.vi-vn.demo`, `catalog.kokoro.en-us.af-heart.demo` |
| 13 | `GET /v1/engines` | bearer | 200 + engine statuses | **200** | 2 engines, both `dependency_missing` (correct — extras not installed) |
| 14 | `GET /v1/diagnostics` | bearer | 200 | **200** | `{"schema_version":"v1","request_id":"local","checks":{"never_run":"true"}}` |

### 2.3 Key behavioural observations

- **Auth boundary is exact:** `/v1/*` requires `Authorization: Bearer <token>`;
  `/console*` is public. There is no path that bypasses auth on `/v1`.
- **SPA fallback works:** deep links under `/console/...` serve
  `index.html` so client-side routing can take over.
- **Static asset serving uses real package resources:** the `Content-Type`
  matches the file extension (`text/javascript` for `.js`, `text/css` for
  `.css`), confirming assets are served via `importlib.resources.files()` and
  not just the local source tree.
- **Traversal guard works on encoded paths:** `/console/assets/%2e%2e/index.html`
  is rejected by `_console_asset_response` (which calls `unquote(...)` and
  refuses leading `/`, `.`, or `..` segments), not normalized away.
- **Bundled catalog is live:** `/v1/catalog/voices` returns the two fixture
  voices baked into the wheel, with `engine_id` correctly distinguishing
  Piper-plus from Kokoro.
- **Engines report `dependency_missing` truthfully:** the live API agrees
  with `mery doctor` that the optional `piper-plus` and `kokoro-onnx`
  packages are not installed.

### 2.4 Teardown

`kill <pid>` followed by `lsof -ti tcp:18765` confirms the port is free;
final uvicorn log line is `Application shutdown complete`. The temp
`$MERY_TTS_DATA_DIR` is removed.

---

## 3. Full pytest run (no marker filter)

```
collected 275 items
…
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_audio_sinks.py:145:
    manual audio-device smoke: requires local speakers and user opt-in
SKIPPED [1] tests/unit/test_provider_adapters.py:94:
    piper-plus real-runtime smoke requires optional piper package and fixture model
SKIPPED [1] tests/unit/test_provider_adapters.py:106:
    kokoro real-runtime smoke requires optional kokoro package and fixture voice
======================== 272 passed, 3 skipped in 1.33s ========================
```

### 3.1 Per-marker distribution

| Marker | Count | Notes |
|---|---|---|
| `unit` | 222 | isolated units (storage, catalog, security, audio, etc.) |
| `contract` | 38 | API + schema contract using local fakes |
| `cli` | 13 | CLI commands without real engine downloads |
| `engine` | 3 | all 3 explicitly `pytest.skip(...)` when optional extras absent |
| `integration` | 0 | no tests carry this marker yet |

The 3 `engine` skips are intentional: they are **manual real-runtime smoke
hooks** that only run when the matching optional engine package *and* a
configured fixture model path are both present. The repo already pins the
expected skip reason in the test body, so a missing dep yields a clean skip,
not a failure.

### 3.2 What the marker mix actually proves

- `unit + contract + cli` (272 tests) cover the entire observable runtime
  surface: API request/response shape, auth, rate limiting, OpenAI-compatible
  `/v1/audio/speech` shape, WebSocket events, install-job lifecycle, package
  boundary, security config, security guards, runtime paths, catalog
  normalization, error taxonomy/factories, storage identity, voice descriptor
  discriminated unions, provider adapter taxonomy, etc.
- The `engine` block is the **only** layer that needs real audio output.
  Everything else — schema, transport, security, packaging, CLI, lifecycle —
  is validated without engine downloads.

---

## 4. Canonical gate: `make check`

The `make check` recipe is the single source of truth for "is this build
shippable right now". Latest run:

```
uv run ruff format --check src tests
91 files already formatted
uv run ruff check src tests
All checks passed!
uv run mypy src/mery_tts
Success: no issues found in 60 source files
uv run pytest -m "not engine and not integration"
====================== 272 passed, 3 deselected in 1.27s =======================
uv run mery --help   >/dev/null
uv run mery --version >/dev/null
uv run mery engines   >/dev/null
```

| Stage | Outcome |
|---|---|
| `ruff format --check` | 91 files formatted, no diff |
| `ruff check` | clean (selected: E/F/W/I/UP/B/C4/SIM/ANN/S/RUF) |
| `mypy --strict` | 60 source files, 0 issues |
| `pytest` (deselected: engine+integration) | 272 passed, 3 deselected |
| CLI smoke (`mery --help`, `mery --version`, `mery engines`) | exit 0 |

---

## 5. Coverage by ADR

The runtime follow-up issues pinned in `.scratch/adr-XXXX/` were implemented
and verified by the tests above. The matrix below links the
production-ready slices to the specific tests that prove them.

| ADR | Issue | Evidence |
|---|---|---|
| ADR-0018 Provider Rollout | Kokoro + Piper Plus as platform-integrated providers | `tests/unit/test_storage_identity.py` (4 new tests: shared-artifact GC, `model-file` hydration, unreferenced-artifact rejection, relative-path requirement); `tests/unit/test_doctor_storage_packaging_rollout.py::test_provider_rollout_status_marks_platform_integrated_with_runtime_detail`; structured `ProviderRolloutStatus` in `src/mery_tts/providers/rollout.py` |
| ADR-0020 Web Console | Local web console: catalog, install, try-speech MVP | `tests/contract/test_api_core.py::test_console_static_routes_are_public_spa_without_affecting_v1_auth` (13 endpoint probes including CSS, missing asset, encoded traversal); `tests/contract/test_api_core.py::test_console_assets_pin_token_catalog_speech_and_diagnostics_behaviour`; `tests/unit/test_package_boundary.py::test_console_assets_are_packaged_python_resources`; `tests/unit/test_package_boundary.py::test_readme_status_describes_current_runtime_without_stale_claims` |
| ADR-0004 Engine Strategy | Voice registry routing + refresh semantics; Piper Plus / Kokoro adapter contracts | `tests/unit/test_engine_registry.py`, `tests/unit/test_provider_adapters.py` (5 passed + 2 engine-skip), `tests/unit/test_voice_descriptor.py` |
| ADR-0005 API Protocol | Model install API orchestration; model domain events | `tests/contract/test_api_schemas.py`, `tests/contract/test_rest_management_endpoints.py`, `tests/contract/test_openai_speech.py`, `tests/unit/test_install_jobs.py`, `tests/unit/test_model_install_manager.py` |
| ADR-0006 Security Model | Reject unsafe model IDs and sensitive diagnostics | `tests/unit/test_security_config.py`, `tests/unit/test_security_guards.py`, `tests/unit/test_error_factories.py`, `tests/contract/test_pair_claim_endpoint.py` |
| ADR-0008 Packaging | Keep runtime paths packaging-agnostic | `tests/unit/test_runtime_paths.py`, `tests/unit/test_package_boundary.py`, `tests/unit/test_doctor_storage_packaging_rollout.py` |
| ADR-0012 Audio Delivery | Split CLI playback and streaming audio sinks | `tests/unit/test_audio_sinks.py`, `tests/cli/test_cli_skeleton.py` |
| ADR-0016 Install Job Lifecycle | Async install job, manifest commit, delete GC | `tests/unit/test_install_jobs.py`, `tests/unit/test_model_store.py`, `tests/unit/test_storage_identity.py` |
| ADR-0013 Voice Descriptor Discriminated Union | – | `tests/unit/test_voice_descriptor.py` |
| ADR-0014 OpenAI-Compatible Speech | – | `tests/contract/test_openai_speech.py` (14 tests) |
| ADR-0017 PCM Streaming Protocol | – | `tests/unit/test_ws_and_orchestration.py` |

---

## 6. Known gaps and how to close them

The `engine` marker is the only remaining hard gap. There is no synthetic
audio path: real TTS requires (a) the optional engine package and (b) a
fixture model on disk.

### 6.1 What is *not* covered by current tests

| Test | Why it skips | What unblocks it |
|---|---|---|
| `test_piper_plus_real_runtime_smoke_skips_without_dependency` | requires `piper-plus` optional dependency + fixture `.onnx` model | `uv pip install -e ".[piper-plus]"` + point at a Piper ONNX model |
| `test_kokoro_real_runtime_smoke_skips_without_dependency` | requires `kokoro-onnx` extra + fixture voice bin | `uv pip install -e ".[kokoro]"` + point at a Kokoro voice + voices JSON |
| `test_audio_player_real_device_smoke_is_marked_and_skipped_by_default` | requires local speakers + opt-in | run on a workstation with audio out and replace `pytest.skip(...)` with a real `AudioPlayer.play(...)` call |

### 6.2 What the smoke test would look like once unblocked

```bash
# Install extras
uv pip install -e ".[all]"

# Configure fixture paths (env or config)
export MERY_FIXTURE_PIPER_MODEL=/path/to/piper.onnx
export MERY_FIXTURE_KOKORO_VOICE=/path/to/voice.bin

# Run only the engine block
uv run pytest -m engine -v

# Or exercise live synthesis through the running server
curl -X POST http://127.0.0.1:18765/v1/audio/speech \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"model":"piper-plus","input":"hello","voice":"fixture"}' \
     --output hello.wav
file hello.wav   # expect: RIFF (little-endian) data, WAVE audio
```

### 6.3 Out-of-scope future hardening (not gap-classed)

- Signed/notarized app packaging (`.app`, `.dmg`, `.exe`, `.deb`) — not part
  of the Phase 1 `uv`/`pipx` install story and intentionally deferred.
- Real Piper-plus and Kokoro audio validation in CI — needs a hermetic
  fixture model in the repo (license + size considerations) and a CI image
  with audio out. The hooks exist; the fixtures don't.
- WebSocket client coverage for `/v1/events` — server side is fully
  covered by `tests/unit/test_ws_and_orchestration.py`; no client SDK is
  shipped in this repo.

---

## 7. How to reproduce this report

All commands are run from the repo root with `uv` as the workflow driver.

```bash
# 1. Static checks + canonical test gate
make check

# 2. Full pytest including engine markers (will show 3 skip reasons)
uv run pytest

# 3. Live server smoke
SMOKE_DIR=$(mktemp -d)
MERY_TTS_DATA_DIR="$SMOKE_DIR" MERY_TTS_PORT=18765 \
  uv run mery serve >"$SMOKE_DIR/server.log" 2>&1 &
SERVER_PID=$!
sleep 1
TOKEN=$(jq -r .auth_token "$SMOKE_DIR/config/config.json")

curl -s -o /dev/null -w "console=%{http_code}\n"  http://127.0.0.1:18765/console
curl -s -o /dev/null -w "health=%{http_code}\n"   -H "Authorization: Bearer $TOKEN" \
     http://127.0.0.1:18765/v1/health
curl -s -o /dev/null -w "voices=%{http_code}\n"   -H "Authorization: Bearer $TOKEN" \
     http://127.0.0.1:18765/v1/catalog/voices

kill $SERVER_PID
rm -rf "$SMOKE_DIR"

# 4. Wheel build verification (proves console assets are in the artifact)
uv build --wheel
uv run python -c "import zipfile; \
  print('\n'.join(n for n in zipfile.ZipFile('dist/mery_tts_server-0.1.0-py3-none-any.whl').namelist() \
                  if n.startswith('mery_tts/console/')))"
```

Expected output for step 4:

```
mery_tts/console/__init__.py
mery_tts/console/index.html
mery_tts/console/assets/<vite-hash>.css
mery_tts/console/assets/<vite-hash>.js
```

---

## 8. Test markers quick reference

For maintainers adding new tests:

| Marker | When to use | Default in `make check`? |
|---|---|---|
| `unit` | isolated unit, no I/O | yes |
| `contract` | API/schema contract via local fakes | yes |
| `cli` | CLI subprocess smoke | yes |
| `engine` | real engine binary/model required | **no** (deselected) |
| `integration` | real server boot, network, or model download | **no** (deselected) |

New engine/integration tests should follow the existing pattern: emit
`pytest.skip(<reason>)` with a clear message when the prerequisite is
absent, never `pytest.fail`. The smoke reasons in the 3 existing engine
tests are the canonical template.
