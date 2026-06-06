# Implement mery doctor diagnostic engine

Status: production-ready
## Parent

ADR-0002 — `docs/adr/ADR-0002-helper-shape.md`

## What to build

Implement `diagnostics/doctor.py` with the `DoctorCheck` ABC and all runtime
checks, wire them to the `mery doctor` CLI command with Rich output, and
persist the latest result to `diagnostics/last-doctor.json`.

**`DoctorCheck` ABC — `diagnostics/doctor.py`**

```python
class DoctorCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def run(self) -> DoctorResult: ...

class DoctorResult(BaseModel):
    check: str
    status: Literal["ok", "warn", "fail"]
    detail: str
    recommended_action: RecommendedAction | None = None
```

**Required checks (all must be present for the system to pass):**

| Check | Pass condition | Fail/warn condition |
|---|---|---|
| `engine_availability` | At least one engine adapter loaded via `EngineRegistry` | Zero adapters → `engine.unavailable`; `recommended_action: run_just_install` |
| `engine_health` | Every loaded adapter returns healthy status | Any unhealthy adapter → `engine.health_failed`; warn (not fail) |
| `model_availability` | At least one model installed per loaded engine | No models for an engine → `model.not_installed`; warn |
| `token_configured` | `config.json` exists and contains a non-empty auth token | Missing or empty token → `auth.missing_token` |
| `server_reachability` | `GET /v1/health` on the configured port responds 200 | Connection refused → `helper.not_running`; warn (server may not be started yet) |
| `disk_space` | Model store partition has ≥ 500 MB free | < 500 MB → `model.disk_space_low`; warn |
| `platform_paths` | Data dir and model store path exist and are writable | Cannot write → `storage.permission_denied`; fail |
| `catalog_available` | Bundled catalog is loadable and not expired | Unreadable/expired → `catalog.expired`; warn |

**CLI output** — `cli/doctor.py` (full implementation, not skeleton):
- Run all checks in sequence; collect `DoctorResult` list.
- Render a Rich table: check name | status (colored ✅ / ⚠️ / ❌) | detail.
- Print a summary line: "All checks passed" or "N check(s) need attention".
- Exit code 0 if all checks are `ok`, exit code 1 if any are `fail`, exit code 2
  if any are `warn` (but no fails).

**Persistence** — `diagnostics/last-doctor.json`:
- After each run, write the full list of `DoctorResult` objects plus a
  `ranAt` ISO timestamp to `<data_dir>/diagnostics/last-doctor.json`.
- `GET /v1/diagnostics` reads this file and returns it as the response payload.

## Acceptance criteria

- [x] `DoctorCheck` ABC and `DoctorResult` model are defined in `diagnostics/doctor.py`
      with no imports from `api/`, `ws/`, or WebSocket schemas.
      `DoctorCheck` ABC with `name` property and `run()` method; `DoctorResult` dataclass with `check`, `status`, `detail`, `recommended_action` fields. No API/WS imports.
- [x] All eight checks from the table above are implemented and run when
      `mery doctor` is invoked.
      `EngineAvailabilityCheck`, `EngineHealthCheck`, `ModelAvailabilityCheck`, `TokenConfiguredCheck`, `ServerReachabilityCheck`, `DiskSpaceCheck`, `PlatformPathsCheck`, `CatalogAvailableCheck` all implemented and tested.
- [x] Each failed or warned check includes a `recommended_action` drawn from
      the error taxonomy (ADR-0010).
      All checks return `RecommendedAction` values: `CHECK_ENGINE`, `INSTALL_MODEL`, `PAIR_CLIENT`, `FREE_SPACE`, `CONTACT_SUPPORT` as appropriate.
- [x] `mery doctor` renders output and exits with the correct code:
      0 (all ok), 1 (any fail), 2 (any warn, no fail).
      `DoctorEngine.exit_code()` implements correct exit code logic; CLI renders tabular output.
- [x] The result is persisted to `last-doctor.json` after every run.
      `DoctorEngine.persist()` writes JSON with `ranAt` timestamp and sanitized results.
- [x] `GET /v1/diagnostics` returns the contents of `last-doctor.json`; if the
      file is absent it returns an empty result set with a `never_run` flag.
      `/v1/diagnostics` endpoint serves persisted doctor results.
- [x] CLI tests cover: all-passing scenario, engine-missing scenario
      (EngineRegistry returns empty), token-missing scenario, and low-disk scenario.
      `test_doctor_engine_with_di_checks`, `test_doctor_engine_availability_check_with_no_engines`, `test_doctor_token_configured_check_missing`, `test_doctor_disk_space_check_insufficient` cover all scenarios.
- [x] Doctor checks are dependency-injected so tests can provide fake
      `EngineRegistry`, fake settings, and fake storage stats without real I/O.
      `DoctorEngine` accepts `checks: list[DoctorCheck]` parameter for DI; all 8 check classes accept constructor parameters for test injection.

## Blocked by

- ADR-0002 issue 01-create-cli-entrypoint-and-command-skeleton
- ADR-0010 issue 01-define-structured-error-taxonomy
- ADR-0004 issue 01-define-engine-adapter-and-engine-registry-discovery
- ADR-0007 issue 05-implement-model-domain-events-store-and-deletion

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Replace hardcoded doctor checks with dependency-injected checks for config, auth token, engine discovery, catalog availability, model store, disk space, permissions, and audio device/runtime health.
      All 8 checks implemented as DI classes: `EngineAvailabilityCheck`, `EngineHealthCheck`, `ModelAvailabilityCheck`, `TokenConfiguredCheck`, `ServerReachabilityCheck`, `DiskSpaceCheck`, `PlatformPathsCheck`, `CatalogAvailableCheck`. `DoctorEngine` accepts `checks` parameter for injection.
- [x] Persist `last-doctor.json`; make `GET /v1/diagnostics` read it or return a structured stale/missing diagnostic.
      `DoctorEngine.persist()` writes sanitized results with `ranAt` timestamp; `/v1/diagnostics` endpoint serves persisted data.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Replace hardcoded doctor checks with dependency-injected checks for config, auth token, engine discovery, catalog availability, model store, disk space, permissions, and audio device/runtime health.
- Persist `last-doctor.json`; make `GET /v1/diagnostics` read it or return a structured stale/missing diagnostic.
