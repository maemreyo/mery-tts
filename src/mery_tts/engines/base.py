from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal, Protocol

from mery_tts.voice.descriptor import VoiceDescriptor

if TYPE_CHECKING:
    from mery_tts.streaming.capabilities import StreamingCapabilityInfo

PCMEncoding = Literal["pcm_s16le", "pcm_f32le"]

# P1 HTTP streaming format — see ADR-0032.
HTTP_PCM_ENCODING: PCMEncoding = "pcm_s16le"


@dataclass(frozen=True, slots=True)
class PCMChunk:
    pcm: bytes
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int = 2
    encoding: PCMEncoding = "pcm_s16le"
    sequence: int = 0


class EngineAdapter(ABC):
    engine_id: ClassVar[str]
    accepted_voice_kinds: ClassVar[frozenset[str]]

    def health(self) -> str:
        return "available"

    def voices(self) -> tuple[VoiceDescriptor, ...]:
        return ()

    def streaming_capability(self) -> StreamingCapabilityInfo:
        """Static baseline streaming capability for this engine.

        ADR-0035: layered source of truth — adapter baseline, then
        installed voice/model metadata, then runtime health. Adapters
        override this to declare their actual streaming contract.
        """
        from mery_tts.streaming.capabilities import (
            StreamingCapability,
            StreamingCapabilityInfo,
        )

        return StreamingCapabilityInfo(
            supported=False,
            mode=StreamingCapability.NOT_SUPPORTED,
            granularity="none",
            true_incremental=False,
            format=HTTP_PCM_ENCODING,
            sample_rates_hz=(),
        )

    def voice_streaming_capability(self, voice: VoiceDescriptor) -> StreamingCapabilityInfo:
        """Voice-aware streaming capability, narrowed by voice metadata.

        ADR-0035: narrows ``sample_rates_hz`` against the voice's known
        native rate when the adapter can introspect the model. The default
        implementation returns the baseline unchanged. Adapters that
        distinguish per-voice rates (Piper-plus) override this to read
        the model's declared ``sample_rate`` and intersect with the
        baseline rates.

        CAVEAT: narrowing requires the voice to be in the adapter's
        resolved-voice cache (see ``register_resolved_voice``). At
        discovery time, before any synthesis has populated the cache,
        this method falls back to the engine baseline. The capability
        endpoint therefore reports the narrowest accurate rates only
        after the voice has been resolved at least once via synthesis.
        """
        _ = voice
        return self.streaming_capability()

    def cancel(self, request_id: str) -> None:
        _ = request_id

    def accepts_voice(self, voice: VoiceDescriptor) -> bool:
        return voice.engine_id == self.engine_id and voice.payload.kind in self.accepted_voice_kinds

    def ensure_voice_supported(self, voice: VoiceDescriptor) -> None:
        if voice.engine_id != self.engine_id:
            message = (
                f"Voice '{voice.voice_id}' targets engine '{voice.engine_id}', "
                f"not '{self.engine_id}'."
            )
            raise ValueError(message)
        if voice.payload.kind not in self.accepted_voice_kinds:
            raise ValueError(
                f"Engine '{self.engine_id}' does not accept voice kind '{voice.payload.kind}'."
            )

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: VoiceDescriptor,
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[PCMChunk]:
        raise NotImplementedError


class EngineEntryPoint(Protocol):
    name: str

    def load(self) -> type[EngineAdapter]: ...


@dataclass(frozen=True, slots=True)
class EngineRegistry:
    adapters: dict[str, EngineAdapter]
    load_warnings: tuple[str, ...] = ()

    @property
    def engine_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.adapters))

    @classmethod
    def from_entry_points(cls, entry_points: Iterable[EngineEntryPoint]) -> EngineRegistry:
        adapters: dict[str, EngineAdapter] = {}
        warnings: list[str] = []
        for entry_point in entry_points:
            try:
                adapter_class = entry_point.load()
                adapter = adapter_class()
            except ImportError as exc:
                warnings.append(f"{entry_point.name}: {exc}")
                continue
            adapters[adapter.engine_id] = adapter
        return cls(adapters=adapters, load_warnings=tuple(warnings))
