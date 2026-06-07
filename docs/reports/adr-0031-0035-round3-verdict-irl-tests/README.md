# ADR-0031–0035 Round-3 Verdict IRL Tests

IRL verification of the 7 verdicts from the Patch 3 re-review
(see commit `4b496b4` for context).

## Files

| File | Purpose |
|---|---|
| `report.md` | Formatted markdown report — verdict-to-evidence map, 18/18 unit tests + 5/5 real-audio integration tests, 6 live HTTP tests, verdict-to-commit map, what was NOT verified IRL |
| `live_http_output.txt` | Raw HTTP responses (status, headers, body) for 6 live tests against `mery serve` on port 8765 |

The smoke test that previously lived at `smoke_test.py` has been
retired and replaced by proper pytest functions — see "Re-run the tests"
below.

## Re-run the tests

```bash
# Unit tests (replaces the old smoke test)
uv run pytest tests/unit/test_streaming_real_coverage.py -v

# Integration test with real Piper model (downloads ~63 MB voice, auto-cleans)
uv run pytest tests/integration/test_streaming_real_audio.py -v -m "engine and integration"

# Full make check (unit tests + lint + typecheck)
make check
```

## Re-run the live HTTP tests

The live HTTP tests require:

1. A running Mery TTS server (`uv run mery serve`)
2. An auth token (printed in `~/Library/Application Support/Mery TTS/config/config.json`)
3. At least one installed voice

To replay the 6 live HTTP tests, see the `curl` invocations in
`report.md` under "Layer 3: Live HTTP server" — just substitute the auth
token from your own config.

## Result

- Unit tests: **18/18 PASS** (all 7 verdicts exercised as proper pytest)
- Integration test: **5/5 PASS** with real Piper `en_US-amy-low` voice —
  first round-3 review to prove actual PCM bytes flow through the full
  pipeline, HTTP transport, and first-byte header derivation
- Live HTTP: server starts, auth works, request shape accepted,
  OpenAI error envelope matches contract, streaming path now reaches
  synthesis after the `voice_aliases` default fix

The only remaining IRL gap is end-to-end HTTP streaming with real audio
over the wire (the dev env has no ONNX model at the resolver path). The
integration test proves the streaming code path emits real bytes when a
real model is present.
