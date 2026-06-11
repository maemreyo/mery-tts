import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from mery_tts.engines.base import EngineAdapter, PCMChunk
from mery_tts.synthesis import MeryRequestOptions, SpeechSynthesisService
from mery_tts.text_normalization import normalize_text_for_locale
from mery_tts.voice import PresetVoicePayload, VoiceDescriptor, VoiceRegistry

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "vietnamese_normalization_cases.json"


class CapturingVietnameseAdapter(EngineAdapter):
    engine_id = "fake-vi"
    accepted_voice_kinds = frozenset({"preset"})

    def __init__(self) -> None:
        self.seen_texts: list[str] = []

    async def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        self.ensure_voice_supported(voice)
        self.seen_texts.append(text)
        yield PCMChunk(pcm=text.encode("utf-8"), sample_rate_hz=24_000, channels=1)


def _fixture_cases() -> list[dict[str, object]]:
    loaded = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(loaded, list)
    return [case for case in loaded if isinstance(case, dict)]


@pytest.mark.parametrize("case", _fixture_cases(), ids=lambda case: str(case["id"]))
def test_vietnamese_normalization_fixtures_are_sanitized(case: dict[str, object]) -> None:
    raw_input = str(case["input"])
    result = normalize_text_for_locale(
        raw_input,
        locale="vi-VN",
        max_segment_chars=int(case["max_segment_chars"]),
    )

    assert result.text == case["expected"]
    assert result.warnings == tuple(case["expected_warnings"])
    assert result.locale == "vi-VN"
    assert raw_input not in str(result.diagnostics())
    assert str(case["expected"]) not in str(result.diagnostics())


@pytest.mark.parametrize("case", _fixture_cases(), ids=lambda case: str(case["id"]))
async def test_vietnamese_fixtures_reach_fake_engine_after_core_normalization(
    case: dict[str, object],
) -> None:
    adapter = CapturingVietnameseAdapter()
    voice = VoiceDescriptor(
        voice_id="voice.vi.fixture",
        engine_id="fake-vi",
        payload=PresetVoicePayload(preset_id="vi-fixture"),
        supported_locales=["vi-VN"],
    )
    registry = VoiceRegistry({"fake-vi": adapter})
    registry.register(voice)
    service = SpeechSynthesisService(voice_registry=registry)

    result = await service.synthesize(
        text=str(case["input"]),
        requested_voice="voice.vi.fixture",
        mery_options=MeryRequestOptions(requested_locale="vi-VN"),
    )

    assert adapter.seen_texts == [case["expected"]]
    assert result.chunks[0].pcm == str(case["expected"]).encode("utf-8")
    assert result.diagnostics.requested_locale == "vi-VN"
    assert result.diagnostics.selected_voice_locale == "vi-VN"
