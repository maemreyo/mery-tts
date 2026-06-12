from __future__ import annotations

from mery_tts.cli.suggestions.models import CommandSuggestion, suggestions_to_json
from mery_tts.cli.suggestions.render import format_human_suggestions
from mery_tts.cli.suggestions.resolver import (
    suggestions_for_install_baseline_cancelled,
    suggestions_for_install_baseline_started,
    suggestions_for_open_console_failure,
    suggestions_for_pair,
    suggestions_for_readiness,
    suggestions_for_serve,
    suggestions_for_setup_recommendation,
    suggestions_for_setup_url,
)

__all__ = [
    "CommandSuggestion",
    "format_human_suggestions",
    "suggestions_for_install_baseline_cancelled",
    "suggestions_for_install_baseline_started",
    "suggestions_for_open_console_failure",
    "suggestions_for_pair",
    "suggestions_for_readiness",
    "suggestions_for_serve",
    "suggestions_for_setup_recommendation",
    "suggestions_for_setup_url",
    "suggestions_to_json",
]
