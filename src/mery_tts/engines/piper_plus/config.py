"""Piper ONNX config JSON reader.

ADR-0024 follow-up: the Piper config JSON has a nested schema. Real
Piper voices (e.g. ``en_US-amy-low``) ship configs like::

    {
      "audio": {"sample_rate": 16000, "quality": "low"},
      "espeak": {"voice": "en-us"},
      "inference": {...}
    }

Some older or third-party configs place ``sample_rate`` at the top
level. This module is the single source of truth for reading Piper
config fields — it knows the schema, descends into ``audio`` first,
falls back to top-level, and never raises on missing or malformed
files (returns ``None`` so the caller can degrade gracefully).

Standalone, dependency-free, and unit-testable in isolation: it does
not import the piper package or any mery_tts module beyond stdlib.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PiperConfigReader:
    """Read fields from a Piper ONNX config JSON file.

    All read methods return ``None`` on any failure (missing file,
    malformed JSON, missing field, wrong type). Callers should treat
    ``None`` as "unknown" and fall back to defaults.

    The reader is stateless and safe to share across threads.
    """

    def read_sample_rate_hz(self, config_path: Path) -> int | None:
        """Read the native sample rate (Hz) from a Piper config JSON.

        Checks ``audio.sample_rate`` first (real Piper schema), then
        falls back to top-level ``sample_rate`` (older configs).
        Returns ``None`` if the file is missing, malformed, or the
        field is absent / not a positive integer.
        """
        data = self._read_json(config_path)
        if data is None:
            return None
        return self._extract_positive_int(data, ("audio", "sample_rate"), ("sample_rate",))

    def _read_json(self, config_path: Path) -> dict[str, Any] | None:
        try:
            text = config_path.read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _extract_positive_int(
        self,
        data: dict[str, Any],
        *paths: tuple[str, ...],
    ) -> int | None:
        """Walk each dotted path; return the first positive int found."""
        for path in paths:
            value: Any = data
            for key in path:
                if not isinstance(value, dict):
                    value = None
                    break
                value = value.get(key)
            if isinstance(value, int) and value > 0:
                return value
        return None


__all__ = ["PiperConfigReader"]
