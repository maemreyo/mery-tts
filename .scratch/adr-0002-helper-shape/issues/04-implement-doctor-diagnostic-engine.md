# Implement mery doctor diagnostic engine

Status: completed

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

- [ ] `DoctorCheck` ABC and `DoctorResult` model are defined in `diagnostics/doctor.py`
      with no imports from `api/`, `ws/`, or WebSocket schemas.
- [ ] All eight checks from the table above are implemented and run when
      `mery doctor` is invoked.
- [ ] Each failed or warned check includes a `recommended_action` drawn from
      the error taxonomy (ADR-0010).
- [ ] `mery doctor` renders a Rich table and exits with the correct code:
      0 (all ok), 1 (any fail), 2 (any warn, no fail).
- [ ] The result is persisted to `last-doctor.json` after every run.
- [ ] `GET /v1/diagnostics` returns the contents of `last-doctor.json`; if the
      file is absent it returns an empty result set with a `never_run` flag.
- [ ] CLI tests cover: all-passing scenario, engine-missing scenario
      (EngineRegistry returns empty), token-missing scenario, and low-disk scenario.
- [ ] Doctor checks are dependency-injected so tests can provide fake
      `EngineRegistry`, fake settings, and fake storage stats without real I/O.

## Blocked by

- ADR-0002 issue 01-create-cli-entrypoint-and-command-skeleton
- ADR-0010 issue 01-define-structured-error-taxonomy
- ADR-0004 issue 01-define-engine-adapter-and-engine-registry-discovery
- ADR-0007 issue 05-implement-model-domain-events-store-and-deletion

## Comments
