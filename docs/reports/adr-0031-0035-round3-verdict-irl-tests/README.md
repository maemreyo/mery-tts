# ADR-0031–0035 Round-3 Verdict IRL Tests

IRL verification of the 7 verdicts from the Patch 3 re-review
(see commit `4b496b4` for context).

## Files

| File | Purpose |
|---|---|
| `report.md` | Formatted markdown report — verdict-to-evidence map, 37/37 smoke test, 6 live HTTP tests, verdict-to-commit map, what was NOT verified IRL |
| `smoke_test.py` | Python smoke test — 37 assertions across 8 sections, exercises real module code paths (real `PiperPlusAdapter`, real config JSON, real `StreamingPipeline`) |
| `smoke_output.txt` | Raw output of `smoke_test.py` — `37/37 passed` |
| `live_http_output.txt` | Raw HTTP responses (status, headers, body) for 6 live tests against `mery serve` on port 8765 |

## Re-run the smoke test

From the repo root, with the project venv active:

```bash
uv run python docs/reports/adr-0031-0035-round3-verdict-irl-tests/smoke_test.py
```

Expected output: `Result: 37/37 passed` (or a list of failures).

The smoke test creates fake model fixtures in `/tmp/mery-smoke/model/`
at runtime — no setup needed.

## Re-run the live HTTP tests

The live HTTP tests require:

1. A running Mery TTS server (`uv run mery serve`)
2. An auth token (printed in `~/Library/Application Support/Mery TTS/config/config.json`)
3. At least one installed voice (the smoke test will see what `voice_streaming_capability` returns for it)

To replay the 6 live HTTP tests, see the `curl` invocations in
`report.md` under "Layer 2: Live HTTP server" — just substitute the auth
token from your own config.

## Result

- Smoke test: **37/37 PASS** (all 7 verdicts exercised, plus 3 supplementary
  http.py private-access checks)
- Live HTTP: server starts, auth works, request shape accepted,
  OpenAI error envelope matches contract

The only IRL gap is end-to-end audio streaming with actual PCM bytes
emitted — the dev env's `piper-plus.vi-vn.demo` voice has no ONNX model
file at the resolved path, and the dev server's `voice_aliases` dict is
empty (defaults to `{}` in `create_app`). Both are env-setup issues, not
code defects: the non-streaming path reaches the synthesis service and
the streaming path reaches the alias resolution step, both at the
correct points in the request lifecycle.
