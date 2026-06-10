"""Smoke testing service for synthesis readiness.

ADR-0025: Smoke uses the same SpeechSynthesisService and runtime cache as normal
synthesis with purpose="smoke" context. Smoke records are sanitized and persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from mery_tts.smoke.record import SmokeRecord, SmokeRecordStore, SmokeStatus
from mery_tts.synthesis import (
    SpeechSynthesisService,
    SynthesisError,
    SynthesisResult,
)

SMOKE_TEXT_EN = "The quick brown fox jumps over the lazy dog."
SMOKE_TEXT_VI = "Chào thế giới."


@dataclass(frozen=True, slots=True)
class SmokeResult:
    """Result of a single voice smoke test."""

    voice_id: str
    engine_id: str
    status: SmokeStatus
    sample_rate_hz: int | None = None
    channels: int | None = None
    duration_ms: int | None = None
    failure_detail: str | None = None
    checked_at: datetime | None = None


class SmokeService:
    """Runs smoke tests through the same synthesis path as normal requests."""

    def __init__(
        self,
        *,
        synthesis_service: SpeechSynthesisService,
        record_store: SmokeRecordStore,
    ) -> None:
        self._service = synthesis_service
        self._store = record_store

    async def smoke_voice(
        self,
        voice_id: str,
        *,
        engine_id: str = "unknown",
        text: str | None = None,
    ) -> SmokeResult:
        """Run a smoke test for a single voice."""
        smoke_text = text or SMOKE_TEXT_EN
        checked_at = datetime.now(UTC)

        try:
            result: SynthesisResult = await self._service.synthesize(
                text=smoke_text,
                requested_voice=voice_id,
                response_format="pcm",
            )
            record = SmokeRecord(
                voice_id=voice_id,
                engine_id=result.diagnostics.selected_engine_id,
                status=SmokeStatus.PASSED,
                checked_at=checked_at,
                sample_rate_hz=result.audio_metadata.sample_rate_hz,
                channels=result.audio_metadata.channels,
                duration_ms=result.audio_metadata.duration_ms,
            )
            self._store.save(record)
            return SmokeResult(
                voice_id=voice_id,
                engine_id=result.diagnostics.selected_engine_id,
                status=SmokeStatus.PASSED,
                sample_rate_hz=result.audio_metadata.sample_rate_hz,
                channels=result.audio_metadata.channels,
                duration_ms=result.audio_metadata.duration_ms,
                checked_at=checked_at,
            )
        except SynthesisError as exc:
            record = SmokeRecord(
                voice_id=voice_id,
                engine_id=engine_id,
                status=SmokeStatus.FAILED,
                checked_at=checked_at,
                failure_detail=str(exc),
            )
            self._store.save(record)
            return SmokeResult(
                voice_id=voice_id,
                engine_id=engine_id,
                status=SmokeStatus.FAILED,
                failure_detail=str(exc),
                checked_at=checked_at,
            )
        except Exception as exc:
            record = SmokeRecord(
                voice_id=voice_id,
                engine_id=engine_id,
                status=SmokeStatus.FAILED,
                checked_at=checked_at,
                failure_detail=str(exc),
            )
            self._store.save(record)
            return SmokeResult(
                voice_id=voice_id,
                engine_id=engine_id,
                status=SmokeStatus.FAILED,
                failure_detail=str(exc),
                checked_at=checked_at,
            )

    async def smoke_providers(
        self,
        *,
        providers: list[str] | None = None,
        voice_ids: list[str] | None = None,
    ) -> list[SmokeResult]:
        """Run smoke tests for specified providers or voices."""
        results: list[SmokeResult] = []
        target_voices: list[tuple[str, str]] = []

        if voice_ids:
            target_voices = [(vid, "unknown") for vid in voice_ids]

        if not target_voices and providers:
            target_voices = self._infer_voices_for_providers(providers)

        for voice_id, engine_id in target_voices:
            result = await self.smoke_voice(voice_id, engine_id=engine_id)
            results.append(result)

        return results

    def _infer_voices_for_providers(self, providers: list[str]) -> list[tuple[str, str]]:
        """Infer default voice IDs for given provider engine IDs."""
        default_voices: dict[str, str] = {
            "piper-plus": "piper-plus.en-us.lessac-low",
            "kokoro": "kokoro.en-us.af-heart.demo",
        }
        return [(default_voices[p], p) for p in providers if p in default_voices]

    def get_record(self, voice_id: str) -> SmokeRecord | None:
        return self._store.get(voice_id)

    def get_all_records(self) -> dict[str, SmokeRecord]:
        return self._store.load_all()


__all__ = [
    "SMOKE_TEXT_EN",
    "SMOKE_TEXT_VI",
    "SmokeResult",
    "SmokeService",
]
