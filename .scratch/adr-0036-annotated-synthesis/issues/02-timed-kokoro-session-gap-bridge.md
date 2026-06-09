# TimedKokoroSession gap bridge

Status: done

## Parent

ADR-0036 — `docs/adr/ADR-0036-annotated-synthesis-word-marks.md`

## Acceptance criteria

- [x] Does NOT subclass `kokoro_onnx.Kokoro`
- [x] `synthesize_annotated(text, voice_preset, speed, lang) -> AnnotatedSynthesisResult`
- [x] Calls `runtime.sess.run(None, inputs)` to capture all ONNX outputs
- [x] `marks=[]` when `outputs` has only one element (standard non-timestamped model)
- [x] `_build_word_marks` maps per-word phoneme token counts to cumulative frame durations
- [x] `onnxruntime>=1.16` added to `kokoro` optional extra in `pyproject.toml`
- [x] Module docstring: gap bridge note

## Outcome

File: `src/mery_tts/engines/kokoro/timed_session.py`

Key decisions:
- Accepts existing `kokoro_onnx.Kokoro` runtime from `KokoroRuntimeCache` — reuses `runtime.sess`, `runtime.voices`, `runtime.tokenizer`. No second ONNX session.
- `_FRAME_MS = 256 / 24_000 * 1000 ≈ 10.67 ms/frame` (HifiGAN standard hop size)
- `_build_word_marks()` phonemizes each word individually to count tokens, accumulates `outputs[1]` frames per word
- ±20% token count slack guard prevents silent drift on abbreviations/numbers
- Exceptions in `_build_word_marks` degrade marks to `[]` — synthesis never crashes due to timing failure

502 tests pass.
