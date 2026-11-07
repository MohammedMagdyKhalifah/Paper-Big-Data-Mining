"""Local inference entry point — frozen contract with app/ (CLAUDE_CODE_ML_RESEARCH_PLAN.md §3).

    from ml.infer import predict_text
    predict_text("رمز التحقق لا يصل عند تسجيل الدخول")

Loads the trained artifacts once per process; never calls the network and never
falls back to mock output. Two backends, chosen by artifacts/.../manifest.json:
  * "sklearn-two-stage" (default; tfidf-baseline-v1 and A4 TF-IDF models): gate + category pipelines
  * "hf-7way" (A4 transformer models): one 7-way classifier over [NO + six categories], run on CPU
The default artifact directory is unchanged (ml/artifacts = tfidf-baseline-v1); select another model with
ML_ARTIFACT_DIR=/path/to/artifact_dir. Scores/thresholds are documented in the model cards.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

CATEGORIES = ("AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER")
LABELS7 = ("NO",) + CATEGORIES

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
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.backend = self.manifest.get("backend", "sklearn-two-stage")
        files = self.manifest["files"]
        self.version = str(self.manifest["model_version"]).strip()
        if not self.version:
            raise RuntimeError("manifest.json has an empty model_version")
        th = self.manifest["thresholds"]
        self.gate_threshold = float(th["gate_decision"])
        self.gate_review_low = float(th["gate_review_low"])
        self.gate_review_high = float(th["gate_review_high"])
        self.category_review = float(th["category_review"])

        if self.backend == "sklearn-two-stage":
            import joblib
            for key in ("gate", "category"):
                if not (root / files[key]).is_file():
                    raise FileNotFoundError(f"Model weights missing: {root / files[key]}")
            self.gate = joblib.load(root / files["gate"])
            self.category = joblib.load(root / files["category"])
            self.pos_index = list(self.gate.classes_).index(1)
            bad = set(self.category.classes_) - set(CATEGORIES)
            if bad:
                raise RuntimeError(f"Unexpected category labels in model: {bad}")
        elif self.backend == "hf-7way":
            mdir = root / files["model_dir"]
            for f in ("config.json", "model.safetensors", "a4_meta.json"):
                if not (mdir / f).is_file():
                    raise FileNotFoundError(f"Model weights missing: {mdir / f}")
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from ml.src.hf_model import HFPredictor
            self.hf = HFPredictor(mdir, device="cpu")
        else:
            raise RuntimeError(f"Unknown backend {self.backend!r} in manifest")

    def scores(self, text: str):
        """Return (complaint_score, category, category_score) — category given even if not a complaint."""
        if self.backend == "sklearn-two-stage":
            p = float(self.gate.predict_proba([text])[0][self.pos_index])
            probs = self.category.predict_proba([text])[0]
            best = int(probs.argmax())
            return p, str(self.category.classes_[best]), float(probs[best])
        P = self.hf.predict_proba([text])[0]
        p = float(1.0 - P[0])
        j = int(P[1:].argmax())
        return p, CATEGORIES[j], float(P[1 + j] / p) if p > 0 else 0.0


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
    p_complaint, cat, cat_score = m.scores(text)
    is_complaint = p_complaint >= m.gate_threshold
    gate_uncertain = m.gate_review_low <= p_complaint < m.gate_review_high

    category = None
    category_score = None
    category_uncertain = False
    if is_complaint:
        category = cat
        category_score = min(max(cat_score, 0.0), 1.0)
        category_uncertain = category_score < m.category_review

    return {
        "is_complaint": bool(is_complaint),
        "complaint_score": round(min(max(p_complaint, 0.0), 1.0), 4),
        "category": category,
        "category_score": None if category_score is None else round(category_score, 4),
        "needs_review": bool(gate_uncertain or category_uncertain),
        "model_version": m.version,
    }
