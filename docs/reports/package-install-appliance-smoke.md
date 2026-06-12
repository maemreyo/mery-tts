# Package-install appliance smoke harness

Status: ADR-0048 P1 release evidence

This harness verifies Mery from a fresh package/tool-install style environment instead of an editable repo checkout. It is release evidence for ADR-0048 issue 01.

## What it proves

The harness creates a temporary virtual environment, installs Mery into that environment, invokes the installed `mery` executable, writes an artifact JSON file, and removes temporary directories unless `--keep-temp` is passed.

It verifies:

- `mery --help`
- `mery --version`
- `mery engines`
- `mery catalog`
- `mery doctor`
- `mery launch --action readiness --json`

These commands prove the package entry point, packaged catalog resources, package-discovered engines, platform data paths, and non-destructive launcher/readiness path are available without importing repo internals.

## Normal release command

```bash
make package-smoke
```

Equivalent direct command:

```bash
uv run python tools/package_smoke/run.py --repo-root . --artifact-dir .scratch/package-smoke
```

The harness writes:

```text
.scratch/package-smoke/package-smoke-result.json
```

## Dry-run command

Use dry-run when validating harness wiring in normal CI or local development without building/installing the package:

```bash
uv run python tools/package_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/package-smoke-dry-run
```

Dry-run records the planned venv/install/command sequence but intentionally skips output substring assertions because commands are not executed.

## Definition of Done mapping

- ADR/contract updated: yes — ADR-0048 issue 01 and this report.
- fake-engine deterministic tests: N/A — harness is package-command evidence, tested by unit tests.
- API contract tests: N/A — no API shape changes.
- CLI or Console proof: yes — installed `mery` command outputs captured in JSON artifact.
- diagnostics/error sanitization tests: N/A — no user input, tokens, private paths, or raw text are emitted beyond temp harness paths.
- docs/help updated: yes — this report.
- optional real-engine smoke: N/A for issue 01; later ADR-0048 slices add real voice smoke.
- privacy gates: yes — artifact contains command stdout/stderr only from non-destructive commands.

## Related

- `docs/adr/ADR-0048-dependable-local-tts-appliance.md`
- `.scratch/adr-0048-dependable-local-tts-appliance/issues/01-package-install-appliance-smoke-harness.md`
- `tools/package_smoke/run.py`
- `tests/unit/test_package_smoke_harness.py`
