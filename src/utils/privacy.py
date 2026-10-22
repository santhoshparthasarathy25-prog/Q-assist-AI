"""Light-touch redaction so obvious identifiers are not stored. This is NOT a full de-identification tool."""
import re

_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"\b(?:\+?44\s?|0)\d{3,4}[\s-]?\d{3}[\s-]?\d{3,4}\b"), "[phone]"),
    (re.compile(r"\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b"), "[nhs-number]"),
    (re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"), "[date]"),
    (re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.I), "[postcode]"),
]


def redact(text: str) -> str:
    for rx, token in _PATTERNS:
        text = rx.sub(token, text)
    return text
