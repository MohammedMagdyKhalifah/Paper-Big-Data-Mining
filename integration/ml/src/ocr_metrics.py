"""CER/WER for OCR evaluation (pure Python). Two normalisations are reported:
  light  : NFKC, Arabic-Indic digits -> ASCII, diacritics/tatweel removed, whitespace collapsed (reading order kept)
  letters: light + P1 letter normalisation (alif/ya/ta-marbuta) + punctuation removed
CER = char edit distance / reference chars; WER = word edit distance / reference words (both on the same norm)."""
from __future__ import annotations

import re
import unicodedata

from ml.src.text import _ALIF, _DIACRITICS, _DIGITS, _TATWEEL

_PUNCT = re.compile(r"[^\w\s]|_")


def norm_light(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").translate(_DIGITS)
    s = _TATWEEL.sub("", _DIACRITICS.sub("", s))
    return re.sub(r"\s+", " ", s).strip()


def norm_letters(s: str) -> str:
    s = norm_light(s)
    s = _ALIF.sub("ا", s).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", s)).strip().lower()


def edit_distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def cer_wer(hyp: str, ref: str, norm=norm_light):
    h, r = norm(hyp), norm(ref)
    ce, cn = edit_distance(h, r), len(r)
    we, wn = edit_distance(h.split(), r.split()), len(r.split())
    return ce, cn, we, wn
