"""Conservative, evidence-based detection of EXPLICITLY named digital systems (registry: configs/systems.yaml).

    from ml.src.systems import find_systems
    find_systems("تطبيق أبشر ما يفتح من أمس")
    # {"status": "identified", "systems": [{"system_id": "absher", ..., "mentions": [{"text": "أبشر", "start": 6, ...}]}], ...}

Rules (transparent, no learned model):
  * a registered alias (multi-word Arabic name or Latin spelling) -> identified
  * an ambiguous name (also an ordinary word: ابشر "sure", صحتي "my health", توكلنا على الله) -> identified only
    with a context cue in the 3 preceding tokens (تطبيق/منصة/موقع/app/...) or in quotes; otherwise listed in
    possible_mentions and NOT identified. exclude_after phrases (توكلنا على ...) drop the match entirely.
  * generic references ("التطبيق", "the app") are reported separately; they never name a system.
  * status: "identified" (>= 1 system), "ambiguous" (only possible mentions) or "unknown" (no named system).
Detection says which systems the text names; it does not say which system failed or why.
Spans are character offsets into the ORIGINAL input string (text[start:end] == mention text).
"""
from __future__ import annotations

import os
import re
import threading
import unicodedata
from pathlib import Path

import yaml

ML = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ML / "configs/systems.yaml"
CUE_WINDOW = 3

_DROP = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ​-‏‪-‮⁦-⁩﻿]")
_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه",
                      **{c: str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}, **{c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}})
_TOKEN = re.compile(r"[^\W_]+")
_LATIN = re.compile(r"[A-Za-z]")
_OPEN_Q, _CLOSE_Q = set("\"'«“‘(["), set("\"'»”’)]")
_PROCLITIC = re.compile(r"^(?:[وف]?[بلك]|[وف])")


def normalize_with_map(text: str):
    """Return (normalised text, index map) with norm[i] coming from text[idx[i]]."""
    out, idx = [], []
    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKC", ch):
            if _DROP.match(c):
                continue
            c = c.translate(_MAP).lower()
            out.append(c)
            idx.extend([i] * len(c))
    return "".join(out), idx


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", normalize_with_map(s)[0]).strip()


def _pattern(alias_norm: str, latin: bool):
    body = r"\s+".join(re.escape(t) for t in alias_norm.split())
    if latin:
        return re.compile(rf"(?<![a-z0-9])(?P<name>{body})(?![a-z0-9])")
    return re.compile(rf"(?<!\w)(?:[وف]?[بلك]|[وف])?(?P<name>{body})(?!\w)")


class Registry:
    def __init__(self, cfg: dict, source: str = "<dict>"):
        self.version = str(cfg.get("version"))
        self.source = source
        self.cues = {norm(c) for lang in ("ar", "en") for c in cfg.get("context_cues", {}).get(lang, [])}
        self.systems, self.patterns, seen = {}, [], {}
        for s in cfg["systems"]:
            sid = s["id"]
            if sid in self.systems:
                raise ValueError(f"duplicate system id {sid!r} in {source}")
            self.systems[sid] = {"system_id": sid, "name_ar": s.get("name_ar"), "name_en": s.get("name_en")}
            excl = [norm(x) for x in s.get("exclude_after", [])]
            for kind in ("aliases", "ambiguous"):
                for a in s.get(kind, []):
                    an = norm(a)
                    if an in seen and seen[an] != sid:
                        raise ValueError(f"alias {a!r} used by both {seen[an]} and {sid}")
                    seen[an] = sid
                    self.patterns.append((sid, kind == "ambiguous", _pattern(an, bool(_LATIN.search(an))), excl))
        gen = [norm(g) for lang in ("ar", "en") for g in cfg.get("generic_references", {}).get(lang, [])]
        self.generic = [_pattern(g, bool(_LATIN.search(g))) for g in gen]

    @classmethod
    def from_yaml(cls, path):
        path = Path(path)
        return cls(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))


_lock = threading.Lock()
_registry = None


def load_registry(path=None) -> Registry:
    """Default registry (cached): ML_SYSTEMS_REGISTRY env var or configs/systems.yaml."""
    global _registry
    if path is not None:
        return Registry.from_yaml(path)
    with _lock:
        if _registry is None:
            _registry = Registry.from_yaml(os.environ.get("ML_SYSTEMS_REGISTRY", DEFAULT_REGISTRY))
    return _registry


def _context(nt, start, end, reg):
    """Return a basis string if an ambiguous name at nt[start:end] has supporting context, else None."""
    before = [m.group() for m in _TOKEN.finditer(nt[:start])][-CUE_WINDOW:]
    for tok in reversed(before):
        if tok in reg.cues or _PROCLITIC.sub("", tok) in reg.cues:
            return f"context_cue:{tok}"
    left, right = nt[:start].rstrip()[-1:], nt[end:].lstrip()[:1]
    if left in _OPEN_Q and right in _CLOSE_Q:
        return "quoted"
    return None


def find_systems(text: str, registry: Registry | None = None) -> dict:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    reg = registry or load_registry()
    nt, idx = normalize_with_map(text)

    def span(s, e):
        return idx[s], idx[e - 1] + 1

    cands = []
    for sid, ambiguous, pat, excl in reg.patterns:
        for m in pat.finditer(nt):
            s, e = m.span("name")
            nxt = _TOKEN.search(nt, e)
            nxt = nxt.group() if nxt and nt[e:nxt.start()].strip() == "" else None
            basis = "registered_alias"
            if ambiguous:
                basis = _context(nt, s, e, reg)
                if basis is None and nxt in excl:
                    continue
                basis = f"ambiguous_name+{basis}" if basis else None
            cands.append((s, e, sid, basis))
    # overlaps: keep confirmed over possible, then the longer match
    cands.sort(key=lambda c: (c[3] is None, -(c[1] - c[0]), c[0]))
    kept = []
    for c in cands:
        if all(c[1] <= k[0] or c[0] >= k[1] for k in kept):
            kept.append(c)
    kept.sort()
    systems, possible = {}, []
    for s, e, sid, basis in kept:
        os_, oe = span(s, e)
        m = {"text": text[os_:oe], "start": os_, "end": oe}
        if basis:
            systems.setdefault(sid, {**reg.systems[sid], "mentions": []})["mentions"].append({**m, "basis": basis})
        else:
            possible.append({"system_id": sid, **m, "reason": "ambiguous name without context (also an ordinary word)"})
    generic = []
    for pat in reg.generic:
        for m in pat.finditer(nt):
            os_, oe = span(*m.span("name"))
            generic.append({"text": text[os_:oe], "start": os_, "end": oe})
    generic.sort(key=lambda g: g["start"])
    status = "identified" if systems else ("ambiguous" if possible else "unknown")
    return {"status": status, "systems": list(systems.values()), "possible_mentions": possible,
            "generic_references": generic, "registry_version": reg.version,
            "method": "registry rules v1 (explicit names only; not a diagnosis)"}
