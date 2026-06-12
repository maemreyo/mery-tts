from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any, cast

REQUIRED_HELP_TOPIC_IDS = frozenset(
    {
        "install-setup",
        "pairing-token",
        "missing-optional-dependency",
        "model-corrupt-reinstall",
        "catalog-invalid",
        "local-only-air-gapped",
        "diagnostics-export",
        "package-upgrade",
        "readiness-recovery-contract",
        "runtime-safety-policy",
        "unsupported-format-locale",
        "provider-unavailable",
    }
)


@dataclass(frozen=True, slots=True)
class HelpTopic:
    topic_id: str
    title: str
    body_format: str
    package_path: str
    body: str


def _help_root() -> resources.abc.Traversable:
    return resources.files(__package__ or "mery_tts.help")


def _manifest_entries() -> list[dict[str, Any]]:
    manifest_path = _help_root().joinpath("manifest.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return cast("list[dict[str, Any]]", payload["topics"])


def list_help_topics() -> tuple[HelpTopic, ...]:
    topics: list[HelpTopic] = []
    for entry in _manifest_entries():
        package_path = str(entry["package_path"])
        body = _help_root().joinpath(package_path).read_text(encoding="utf-8")
        topics.append(
            HelpTopic(
                topic_id=str(entry["topic_id"]),
                title=str(entry["title"]),
                body_format=str(entry["body_format"]),
                package_path=package_path,
                body=body,
            )
        )
    return tuple(topics)


def get_help_topic(topic_id: str) -> HelpTopic:
    for topic in list_help_topics():
        if topic.topic_id == topic_id:
            return topic
    raise KeyError(f"unknown help topic: {topic_id}")


__all__ = ["REQUIRED_HELP_TOPIC_IDS", "HelpTopic", "get_help_topic", "list_help_topics"]
