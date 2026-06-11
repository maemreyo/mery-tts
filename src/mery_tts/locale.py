import re
from typing import Annotated

from pydantic import AfterValidator

_LOCALE_PATTERN = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


def normalize_bcp47_locale(value: str) -> str:
    """Normalize the subset of BCP-47 tags Mery exposes in public contracts."""
    raw = value.strip()
    if not raw or not _LOCALE_PATTERN.fullmatch(raw):
        raise ValueError("locale must be a valid BCP-47 tag")
    parts = raw.split("-")
    normalized = [parts[0].lower()]
    for index, part in enumerate(parts[1:], start=1):
        if index == 1 and len(part) == 2 and part.isalpha():
            normalized.append(part.upper())
        elif len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


def normalize_bcp47_locales(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        tag = normalize_bcp47_locale(value)
        if tag not in seen:
            normalized.append(tag)
            seen.add(tag)
    return normalized


Bcp47Locale = Annotated[str, AfterValidator(normalize_bcp47_locale)]
