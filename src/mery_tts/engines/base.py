from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from typing import ClassVar, Protocol

from mery_tts.voice.descriptor import VoiceDescriptor


@dataclass(frozen=True, slots=True)
class PCMChunk:
    pcm: bytes
    sample_rate_hz: int
    channels: int


class EngineAdapter(ABC):
    engine_id: ClassVar[str]
    accepted_voice_kinds: ClassVar[frozenset[str]]

    def health(self) -> str:
        return "available"

    def voices(self) -> tuple[VoiceDescriptor, ...]:
        return ()

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
    def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]:
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
    def from_entry_points(cls, entry_points: Iterable[EngineEntryPoint]) -> "EngineRegistry":
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
