# VoiceCapabilities schema and GET /v1/voices/installed

Status: done

## Parent

ADR-0036 — `docs/adr/ADR-0036-annotated-synthesis-word-marks.md`

## Acceptance criteria

- [x] `VoiceCapabilitiesVo(BaseModel, frozen=True)` with `word_marks: bool = False`
- [x] `VoiceSummary.capabilities: VoiceCapabilitiesVo | None = None`
- [x] `GET /v1/voices/installed` populates `word_marks=True` for Kokoro voices
- [x] Backward compatible — nullable field

## Outcome

File: `src/mery_tts/schemas/v1.py`

Three new models added: `VoiceCapabilitiesVo`, `SpeechMarkVo`, `AnnotatedSpeechResponse`.

`app.py` ~line 435:
```python
capabilities=VoiceCapabilitiesVo(
    word_marks=isinstance(engine_registry.adapters.get(voice.engine_id), AnnotatedSynthesisCapable)
)
```

Contract test `tests/contract/test_rest_management_endpoints.py` updated to assert `capabilities: {word_marks: True}`. 502 tests pass.
