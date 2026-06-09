# KokoroAdapter implements AnnotatedSynthesisCapable

Status: done

## Parent

ADR-0036 — `docs/adr/ADR-0036-annotated-synthesis-word-marks.md`

## Acceptance criteria

- [x] `KokoroAdapter` implements `async synthesize_annotated(text, voice) -> AnnotatedSynthesisResult`
- [x] `isinstance(adapter, AnnotatedSynthesisCapable)` returns `True`
- [x] Dispatches to `TimedKokoroSession` via `asyncio.to_thread`
- [x] `_timed_sessions: dict[str, TimedKokoroSession]` cached per voice_id
- [x] `synthesize()` unchanged

## Outcome

File: `src/mery_tts/engines/kokoro/adapter.py`

Design deviation: session not injected at construction (would require touching all test fixtures). Instead `_get_or_create_timed_session(voice_id, runtime)` lazily wraps the runtime already held in `KokoroRuntimeCache`. `KokoroAdapter` always satisfies `AnnotatedSynthesisCapable` — Piper adapter never does, so `word_marks` stays `False` for Piper automatically.

502 tests pass.
