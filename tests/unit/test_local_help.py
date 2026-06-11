from importlib import resources

import pytest

from mery_tts.help import REQUIRED_HELP_TOPIC_IDS, get_help_topic, list_help_topics


def test_local_help_manifest_covers_required_offline_recovery_topics() -> None:
    topics = list_help_topics()
    topic_ids = {topic.topic_id for topic in topics}

    assert topic_ids == REQUIRED_HELP_TOPIC_IDS
    assert all(topic.title for topic in topics)
    assert all(topic.body_format == "markdown" for topic in topics)
    assert all(topic.package_path.startswith("topics/") for topic in topics)


def test_local_help_topics_are_accessible_offline_from_package_resources() -> None:
    topic = get_help_topic("pairing-token")

    assert topic.topic_id == "pairing-token"
    assert "Pairing" in topic.title
    assert "internet" not in topic.body.lower()
    assert "mery pair" in topic.body


def test_local_help_rejects_unknown_topic_ids() -> None:
    with pytest.raises(KeyError, match="unknown help topic"):
        get_help_topic("missing-topic")


def test_local_help_manifest_and_topic_files_are_packaged() -> None:
    help_root = resources.files("mery_tts.help")

    assert help_root.joinpath("manifest.json").is_file()
    for topic in list_help_topics():
        assert help_root.joinpath(topic.package_path).is_file()
