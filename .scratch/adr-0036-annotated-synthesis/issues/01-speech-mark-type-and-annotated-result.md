# SpeechMark type and AnnotatedSynthesisResult

Status: done

## Parent

ADR-0036 — `docs/adr/ADR-0036-annotated-synthesis-word-marks.md`

## Acceptance criteria

- [x] `SpeechMark` frozen dataclass: `word: str`, `start_ms: int`, `end_ms: int`
- [x] `AnnotatedSynthesisResult`: `chunks: list[PCMChunk]`, `marks: list[SpeechMark]`
- [x] `AnnotatedSynthesisCapable` — `@runtime_checkable` Protocol with `async synthesize_annotated()`
- [x] `isinstance(engine, AnnotatedSynthesisCapable)` works without nominal inheritance
- [x] No circular imports — only `PCMChunk` from `engines/base.py`

## Outcome

File: `src/mery_tts/engines/annotated.py`

Named `annotated.py` (not `marks.py`) to avoid shadowing Python stdlib. All three types in one module. Protocol is `async` — `synthesize_annotated` is a coroutine matching the `synthesize` pattern in `EngineAdapter`. 502 tests pass.
