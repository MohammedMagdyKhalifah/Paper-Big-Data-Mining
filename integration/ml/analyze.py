"""Unified local analysis of a complaint given as text and/or a screenshot (P1). For FastAPI (app/) use.

    from ml.analyze import analyze, extract_text
    analyze(text="تطبيق أبشر ما يفتح")                    # typed complaint
    analyze(image="shot.png")                            # screenshot: OCR -> classify -> systems
    ocr = extract_text("shot.png")                       # two-step flow: show OCR text to the user ...
    analyze(image_ocr=ocr, corrected_text="...")         # ... then classify the user-corrected text

The trained model's output is ml.infer.predict_text(...) UNCHANGED (six-field contract) under "prediction".
OCR text, OCR metadata, detected systems, evidence spans and error-screen signals live beside it in this
separate structure (schema "p1-analysis-v1", documented in reports/p1_integration_notes.md). All local/offline.
"""
from __future__ import annotations

import re
import threading
import time
from pathlib import Path

import yaml

from ml.infer import predict_text
from ml.src.ocr import extract_text
from ml.src.systems import find_systems, norm, normalize_with_map

SCHEMA_VERSION = "p1-analysis-v1"
_CUES_PATH = Path(__file__).resolve().parent / "configs/error_cues.yaml"
_lock = threading.Lock()
_cues = None

__all__ = ["analyze", "extract_text", "find_systems", "error_cues", "narrative_markers", "warmup", "SCHEMA_VERSION"]


def _cue_patterns():
    global _cues
    with _lock:
        if _cues is None:
            cfg = yaml.safe_load(_CUES_PATH.read_text(encoding="utf-8"))

            def compile_(words):
                out = []
                for c in sorted({norm(x) for x in words}, key=len, reverse=True):
                    body = r"\s+".join(re.escape(t) for t in c.split())
                    out.append((c, re.compile(rf"(?<!\w)(?:[وف]?[بلك]|[وف])?({body})(?!\w)")))
                return out
            _cues = (compile_(cfg["ar"] + cfg["en"]),
                     compile_(cfg["narrative_markers"]["ar"] + cfg["narrative_markers"]["en"]))
    return _cues


def narrative_markers(text: str) -> list:
    """First-person/narrative markers found in `text` (a user's description rather than a bare error screen)."""
    nt = normalize_with_map(text)[0]
    return [c for c, pat in _cue_patterns()[1] if pat.search(nt)]


def error_cues(text: str) -> list:
    """Error-message cue matches [{text, start, end, cue}] (non-overlapping, longest first) in `text`."""
    nt, idx = normalize_with_map(text)
    found = []
    for cue, pat in _cue_patterns()[0]:
        for m in pat.finditer(nt):
            s, e = m.span(1)
            if all(e <= f[0] or s >= f[1] for f in found):
                found.append((s, e, cue))
    return [{"text": text[idx[s]:idx[e - 1] + 1], "start": idx[s], "end": idx[e - 1] + 1, "cue": c} for s, e, c in sorted(found)]


def warmup(ocr_engine: str | None = None) -> dict:
    """Load the classifier, OCR engine, registry and cue lexicon once (call at app start-up; cold load ~20 s)."""
    from ml.src.ocr import get_engine
    from ml.src.systems import load_registry
    t0 = time.perf_counter()
    version = predict_text("تجربة تحميل النموذج")["model_version"]
    engine = get_engine(ocr_engine).name
    load_registry()
    _cue_patterns()
    return {"model_version": version, "ocr_engine": engine, "elapsed_s": round(time.perf_counter() - t0, 2)}


def analyze(text: str | None = None, image=None, *, image_ocr: dict | None = None, corrected_text: str | None = None,
            ocr_engine: str | None = None) -> dict:
    """Analyse typed text and/or a screenshot.

    text           : the user's own complaint text (optional)
    image          : PNG/JPEG path, bytes or PIL.Image (optional) -> OCR'd here
    image_ocr      : a previous extract_text() result (instead of `image`, e.g. after showing it to the user)
    corrected_text : the user's correction of the OCR text; replaces the OCR text for classification
    Raises ValueError if nothing usable was given, TypeError for wrong types; OCRUnavailableError /
    FileNotFoundError (model artifacts) are deployment errors and propagate.
    """
    t0 = time.perf_counter()
    if text is not None and not isinstance(text, str):
        raise TypeError(f"text must be str or None, got {type(text).__name__}")
    if corrected_text is not None and not isinstance(corrected_text, str):
        raise TypeError("corrected_text must be str or None")
    if image is not None and image_ocr is not None:
        raise ValueError("give either image or image_ocr, not both")
    user_text = (text or "").strip()
    if not user_text and image is None and image_ocr is None and not (corrected_text or "").strip():
        raise ValueError("nothing to analyse: give text, image, image_ocr or corrected_text")

    timing = {}
    ocr = None
    if image is not None:
        ocr = extract_text(image, engine=ocr_engine)
        timing["ocr_ms"] = ocr["elapsed_ms"]
    elif image_ocr is not None:
        if not isinstance(image_ocr, dict) or "status" not in image_ocr:
            raise TypeError("image_ocr must be a dict returned by extract_text()")
        ocr = dict(image_ocr)
    has_image = ocr is not None or corrected_text is not None

    image_text, image_source = "", None
    if corrected_text is not None and corrected_text.strip():
        image_text, image_source = corrected_text.strip(), "ocr_corrected"
    elif ocr is not None and ocr["status"] == "ok":
        image_text, image_source = ocr["text"].strip(), "ocr"
    if ocr is not None:
        ocr["corrected_text"] = corrected_text
        ocr["used_for_classification"] = image_source

    parts = [p for p in (user_text, image_text) if p]
    classified = "\n".join(parts) if parts else None
    source = "+".join(s for s, p in (("user_text", user_text), (image_source, image_text)) if p) or None

    prediction = systems = None
    cues, narrative, notes = [], [], []
    if classified:
        t1 = time.perf_counter()
        prediction = predict_text(classified)
        timing["classify_ms"] = round((time.perf_counter() - t1) * 1000, 1)
        t1 = time.perf_counter()
        systems = find_systems(classified)
        timing["systems_ms"] = round((time.perf_counter() - t1) * 1000, 2)
        cues = error_cues(image_text) if image_text else []
        narrative = narrative_markers(image_text) if image_text else []
        if user_text and image_text:
            off = len(user_text) + 1
            cues = [{**c, "start": c["start"] + off, "end": c["end"] + off} for c in cues]

    ocr_needs_review = ocr is not None and image_source == "ocr" and bool(ocr.get("low_confidence"))
    needs_context = False
    if classified is None:
        kind = "ocr_failed" if ocr is not None and ocr["status"] == "failed" else "no_text"
        notes.append("No readable text: nothing was classified." if kind == "no_text"
                     else f"OCR failed ({ocr['error']['code']}): nothing was classified.")
    elif has_image and not user_text and cues and not narrative:
        kind, needs_context = "error_screen_signal", True
        notes.append("Screenshot of an error message without the user's own description: the model output is "
                     "attached, but the screen alone does not say what the user was doing; ask for context.")
    else:
        kind = "complaint" if prediction["is_complaint"] else "not_complaint"
    if ocr is not None and ocr["status"] == "failed" and classified:
        notes.append(f"OCR failed ({ocr['error']['code']}); only the typed text was classified.")
    if ocr_needs_review:
        notes.append("OCR confidence is low: show the extracted text to the user for correction.")
    if systems and systems["status"] == "ambiguous":
        notes.append("A registered system name appears only as an ordinary word without context: not identified.")

    timing["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_kind": kind,
        "input": {"has_user_text": bool(user_text), "has_image": has_image, "text_source": source, "classified_text": classified},
        "prediction": prediction,
        "systems": systems,
        "signals": {"error_message_cues": cues, "narrative_markers": narrative, "needs_user_context": needs_context, "ocr_needs_review": ocr_needs_review},
        "ocr": ocr,
        "notes": notes,
        "timing_ms": timing,
    }
