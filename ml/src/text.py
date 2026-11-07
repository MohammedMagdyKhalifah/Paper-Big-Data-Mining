"""Conservative Arabic text processing: PII masking and normalization variants.

P0 = minimal cleanup + privacy masking (reference variant).
P1 = P0 + controlled Arabic orthographic normalization.
Negation particles (لا، ما، مش، مو، ليس، مافي ...) are never removed: no stop-word
removal is performed in P0/P1.
"""
from __future__ import annotations

import re
import unicodedata

# Arabic-Indic (U+0660..) and Extended Arabic-Indic / Persian (U+06F0..) digits -> ASCII.
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

_ZERO_WIDTH = re.compile(r"[​-‏‪-‮⁦-⁩﻿]")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_WS = re.compile(r"\s+")

_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_MENTION = re.compile(r"(?<!\w)@\w+")
# Saudi mobile numbers: 05xxxxxxxx, 5xxxxxxxx, +9665xxxxxxxx, 009665xxxxxxxx (spaces/dashes allowed).
_PHONE = re.compile(r"(?<!\d)(?:\+?966|00966|0)?[\s-]?5(?:[\s-]?\d){8}(?!\d)")
# Any remaining long digit run (national/iqama IDs, request numbers, card numbers).
_LONG_NUM = re.compile(r"(?<!\d)\d(?:[\s-]?\d){6,}(?!\d)")

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = re.compile(r"ـ")
_ALIF = re.compile(r"[أإآٱ]")
_REPEAT = re.compile(r"(.)\1{2,}")

_ARABIC_LETTER = re.compile(r"[ء-يٮ-ۓۺ-ۿ]")
_LATIN_LETTER = re.compile(r"[A-Za-z]")


def mask_pii(text: str) -> str:
    """Replace identifying strings with placeholders. Order matters (URL/email before numbers)."""
    text = _URL.sub(" [URL] ", text)
    text = _EMAIL.sub(" [EMAIL] ", text)
    text = _MENTION.sub(" [USER] ", text)
    text = _PHONE.sub(" [PHONE] ", text)
    text = _LONG_NUM.sub(" [NUM] ", text)
    return text


def p0(text: str) -> str:
    """Minimal cleanup + required privacy masking."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_DIGITS)
    text = _ZERO_WIDTH.sub("", text)
    text = _CONTROL.sub(" ", text)
    text = mask_pii(text)
    return _WS.sub(" ", text).strip()


def p1(text: str) -> str:
    """P0 + controlled Arabic letter/diacritic normalization."""
    text = p0(text)
    text = _DIACRITICS.sub("", text)
    text = _TATWEEL.sub("", text)
    text = _ALIF.sub("ا", text)
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = _REPEAT.sub(r"\1", text)
    text = text.lower()
    return _WS.sub(" ", text).strip()


VARIANTS = {"P0": p0, "P1": p1}


def preprocess(texts, variant: str = "P1"):
    """Vectorised entry point used inside sklearn pipelines (FunctionTransformer)."""
    fn = VARIANTS[variant]
    return [fn(t) for t in texts]


def preprocess_p0(texts):
    return preprocess(texts, "P0")


def preprocess_p1(texts):
    return preprocess(texts, "P1")


def arabic_ratio(text: str) -> float:
    """Share of Arabic letters among Arabic+Latin letters (0 if no letters)."""
    ar = len(_ARABIC_LETTER.findall(text))
    la = len(_LATIN_LETTER.findall(text))
    return ar / (ar + la) if (ar + la) else 0.0


def exclusion_reason(text) -> str | None:
    """Screening rule for the research corpus (not applied at inference)."""
    if not isinstance(text, str) or not text.strip():
        return "empty"
    cleaned = p0(text)
    if not (_ARABIC_LETTER.search(cleaned) or _LATIN_LETTER.search(cleaned)):
        return "no_letters_emoji_only"
    if arabic_ratio(cleaned) < 0.5:
        return "not_predominantly_arabic"
    if len(cleaned.split()) < 2:
        return "too_short"
    return None
