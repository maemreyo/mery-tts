from importlib.metadata import entry_points

from mery_tts.engines.base import EngineRegistry

ENTRY_POINT_GROUP = "mery_tts.engines"


def discover_engine_registry() -> EngineRegistry:
    discovered = entry_points().select(group=ENTRY_POINT_GROUP)
    return EngineRegistry.from_entry_points(discovered)


__all__ = ["ENTRY_POINT_GROUP", "discover_engine_registry"]
