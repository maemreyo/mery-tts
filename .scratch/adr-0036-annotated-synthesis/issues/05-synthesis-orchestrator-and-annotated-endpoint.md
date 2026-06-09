# SynthesisOrchestrator and POST /v1/audio/speech/annotated

Status: done

## Parent

ADR-0036 — `docs/adr/ADR-0036-annotated-synthesis-word-marks.md`

## Acceptance criteria

- [x] `POST /v1/audio/speech/annotated` route
- [x] Dispatches to `synthesize_annotated()` when `isinstance(adapter, AnnotatedSynthesisCapable)`
- [x] Falls back to standard synthesis with `marks=[], marks_available=false`
- [x] Response: `{ audio_b64, sample_rate, marks, marks_available }`
- [x] `max_text_chars` guard (413) same as `/v1/audio/speech`
- [x] `/v1/audio/speech` unchanged

## Outcome

Design deviation: no separate `engines/orchestrator.py`. Dispatch lives in `src/mery_tts/api/openai/speech.py` as `synthesize_annotated_openai_speech()`. 15 lines, co-located with existing synthesis functions.

Route `src/mery_tts/api/app.py` line ~1032:
- Returns `JSONResponse(AnnotatedSpeechResponse(...).model_dump())`
- Audio base64-encoded via `base64.b64encode(wav_bytes).decode()`

502 tests pass.
