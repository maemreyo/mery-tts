import re
import unicodedata
from dataclasses import dataclass

from mery_tts.locale import normalize_bcp47_locale

NORMALIZER_VERSION = "core-text-v1"

PUNCTUATION_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2026": "...",
    }
)
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class TextNormalizationResult:
    text: str
    locale: str
    normalizer_version: str
    categories_applied: tuple[str, ...]
    segments: tuple[str, ...]
    warnings: tuple[str, ...]
    length_before: int
    length_after: int

    def diagnostics(self) -> dict[str, str | int]:
        return {
            "locale": self.locale,
            "normalizer_version": self.normalizer_version,
            "categories_applied": ",".join(self.categories_applied),
            "length_before": self.length_before,
            "length_after": self.length_after,
            "segment_count": len(self.segments),
            "warnings": ",".join(self.warnings),
        }


def normalize_text_for_locale(
    text: str,
    *,
    locale: str,
    max_segment_chars: int = 500,
) -> TextNormalizationResult:
    normalized_locale = normalize_bcp47_locale(locale)
    length_before = len(text)
    normalized = unicodedata.normalize("NFKC", text).translate(PUNCTUATION_TRANSLATION)
    normalized = _WHITESPACE.sub(" ", normalized).strip()
    segments = _segment_text(normalized)
    warnings = tuple(
        {"segment_too_long" for segment in segments if len(segment) > max_segment_chars}
    )
    categories = ["unicode_nfkc", "punctuation_ascii", "whitespace_collapse"]
    if len(segments) > 1:
        categories.append("segmentation")
    return TextNormalizationResult(
        text=normalized,
        locale=normalized_locale,
        normalizer_version=NORMALIZER_VERSION,
        categories_applied=tuple(categories),
        segments=segments,
        warnings=warnings,
        length_before=length_before,
        length_after=len(normalized),
    )


def _segment_text(text: str) -> tuple[str, ...]:
    segments = tuple(segment.strip() for segment in _SENTENCE_BOUNDARY.split(text))
    return tuple(segment for segment in segments if segment) or (text,)
