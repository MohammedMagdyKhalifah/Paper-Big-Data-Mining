"""Local inference entry point — frozen contract with app/ (CLAUDE_CODE_ML_RESEARCH_PLAN.md §3).

    from ml.infer import predict_text
    predict_text("رمز التحقق لا يصل عند تسجيل الدخول")

Loads the trained artifacts once per process; never calls the network and never
falls back to mock output. Scores and thresholds are documented in
ml/reports/model_card.md.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

CATEGORIES = ("AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER")

_DEFAULT_DIR = Path(__file__).resolve().parent / "artifacts"
_lock = threading.Lock()
_model = None


def _artifact_dir() -> Path:
    return Path(os.environ.get("ML_ARTIFACT_DIR", _DEFAULT_DIR))


class _Model:
    def __init__(self, root: Path):
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"Model manifest not found at {manifest_path}. Train the model first "
                "(see ml/README.md); no mock predictions are served."
            )
        import joblib

        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = self.manifest["files"]
        for key in ("gate", "category"):
            if not (root / files[key]).is_file():
                raise FileNotFoundError(f"Model weights missing: {root / files[key]}")
        self.gate = joblib.load(root / files["gate"])
        self.category = joblib.load(root / files["category"])
        self.version = str(self.manifest["model_version"]).strip()
        if not self.version:
            raise RuntimeError("manifest.json has an empty model_version")
        th = self.manifest["thresholds"]
        self.gate_threshold = float(th["gate_decision"])
        self.gate_review_low = float(th["gate_review_low"])
        self.gate_review_high = float(th["gate_review_high"])
        self.category_review = float(th["category_review"])
        self.pos_index = list(self.gate.classes_).index(1)
        bad = set(self.category.classes_) - set(CATEGORIES)
        if bad:
            raise RuntimeError(f"Unexpected category labels in model: {bad}")


def _get_model() -> _Model:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = _Model(_artifact_dir())
    return _model


def _reset_cache() -> None:
    """Testing helper: forget the loaded model."""
    global _model
    with _lock:
        _model = None


def predict_text(text: str) -> dict:
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    if not text.strip():
        raise ValueError("text is empty or whitespace only")

    m = _get_model()
    p_complaint = float(m.gate.predict_proba([text])[0][m.pos_index])
    is_complaint = p_complaint >= m.gate_threshold
    gate_uncertain = m.gate_review_low <= p_complaint < m.gate_review_high

    category = None
    category_score = None
    category_uncertain = False
    if is_complaint:
        probs = m.category.predict_proba([text])[0]
        best = int(probs.argmax())
        category = str(m.category.classes_[best])
        category_score = float(probs[best])
        category_uncertain = category_score < m.category_review

    return {
        "is_complaint": bool(is_complaint),
        "complaint_score": round(p_complaint, 4),
        "category": category,
        "category_score": None if category_score is None else round(category_score, 4),
        "needs_review": bool(gate_uncertain or category_uncertain),
        "model_version": m.version,
    }
