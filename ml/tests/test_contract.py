"""Contract tests for ml.infer.predict_text.

Two layers:
  * `stub_artifacts`  — a tiny STUB model trained on 8 toy sentences, written to a temp dir.
                        It exists ONLY to test the output shape; it is NOT the real model.
  * `real` tests      — run against ml/artifacts (the trained model) and are skipped
                        with an explicit reason until training has produced it.
"""
import json
import time

import joblib
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

import ml.infer as infer

KEYS = {"is_complaint", "complaint_score", "category", "category_score", "needs_review", "model_version"}


def _check_shape(r):
    assert set(r) == KEYS
    assert isinstance(r["is_complaint"], bool)
    assert isinstance(r["needs_review"], bool)
    assert isinstance(r["model_version"], str) and r["model_version"].strip()
    assert r["category"] is None or r["category"] in infer.CATEGORIES
    for k in ("complaint_score", "category_score"):
        assert r[k] is None or (isinstance(r[k], float) and 0.0 <= r[k] <= 1.0)
    if not r["is_complaint"]:
        assert r["category"] is None and r["category_score"] is None


@pytest.fixture
def stub_artifacts(tmp_path, monkeypatch):
    gate = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3)), LogisticRegression())
    gate.fit(["ما يفتح التطبيق", "رمز التحقق ما يوصل", "بطيء جدا", "تطبيق رائع", "شكرا جزيلا", "ممتاز"],
             [1, 1, 1, 0, 0, 0])
    cat = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3)), LogisticRegression())
    cat.fit(["رمز التحقق", "كلمة المرور", "بطيء", "يحمل وقت طويل"], ["AUTH", "AUTH", "PERF", "PERF"])
    joblib.dump(gate, tmp_path / "gate.joblib")
    joblib.dump(cat, tmp_path / "category.joblib")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "model_version": "STUB-test-only",
        "files": {"gate": "gate.joblib", "category": "category.joblib"},
        "thresholds": {"gate_decision": 0.5, "gate_review_low": 0.35, "gate_review_high": 0.65,
                       "category_review": 0.6},
    }))
    monkeypatch.setenv("ML_ARTIFACT_DIR", str(tmp_path))
    infer._reset_cache()
    yield tmp_path
    infer._reset_cache()


def test_empty_raises_before_loading(monkeypatch, tmp_path):
    monkeypatch.setenv("ML_ARTIFACT_DIR", str(tmp_path))
    infer._reset_cache()
    for t in ["", "   ", "\n\t"]:
        with pytest.raises(ValueError):
            infer.predict_text(t)
    with pytest.raises(TypeError):
        infer.predict_text(None)


def test_missing_artifacts_is_explicit_error(monkeypatch, tmp_path):
    monkeypatch.setenv("ML_ARTIFACT_DIR", str(tmp_path / "nope"))
    infer._reset_cache()
    with pytest.raises(FileNotFoundError):
        infer.predict_text("التطبيق بطيء")
    infer._reset_cache()


def test_missing_weights_is_explicit_error(stub_artifacts):
    (stub_artifacts / "category.joblib").unlink()
    infer._reset_cache()
    with pytest.raises(FileNotFoundError):
        infer.predict_text("التطبيق بطيء")


def test_stub_shape_and_noncomplaint(stub_artifacts):
    for t in ["رمز التحقق ما يوصل", "تطبيق رائع شكرا", "the app is بطيء"]:
        _check_shape(infer.predict_text(t))
    assert infer.predict_text("tطبيق")["model_version"] == "STUB-test-only"


def test_stub_loaded_once(stub_artifacts):
    infer.predict_text("بطيء")
    first = infer._model
    for _ in range(20):
        infer.predict_text("بطيء")
    assert infer._model is first


# ---------------- real trained model (ml/artifacts) ----------------

def _real_available():
    return (infer._DEFAULT_DIR / "manifest.json").is_file()


real = pytest.mark.skipif(not _real_available(), reason="trained artifacts not built yet (run ml/scripts/train.py)")


@pytest.fixture
def real_model(monkeypatch):
    monkeypatch.delenv("ML_ARTIFACT_DIR", raising=False)
    infer._reset_cache()
    yield
    infer._reset_cache()


@real
def test_real_auth_complaint(real_model):
    r = infer.predict_text("رمز التحقق لا يصل عند تسجيل الدخول")
    _check_shape(r)
    assert r["model_version"] != "STUB-test-only"
    assert r["is_complaint"] is True and r["category"] == "AUTH"


@real
def test_real_perf_complaint(real_model):
    r = infer.predict_text("التطبيق بطيء جدا والصفحة تحمل وقت طويل")
    _check_shape(r)
    assert r["is_complaint"] is True and r["category"] == "PERF"


@real
def test_real_non_complaint(real_model):
    r = infer.predict_text("تطبيق رائع وسهل الاستخدام شكرا لكم")
    _check_shape(r)
    assert r["is_complaint"] is False and r["category"] is None


@real
def test_real_mixed_language(real_model):
    _check_shape(infer.predict_text("الـ OTP ما يوصلني when I try to login"))


@real
def test_real_repeated_calls_fast(real_model):
    infer.predict_text("التطبيق بطيء")
    first = infer._model
    t0 = time.perf_counter()
    for _ in range(50):
        _check_shape(infer.predict_text("التطبيق يقفل فجأة"))
    assert infer._model is first
    assert (time.perf_counter() - t0) / 50 < 0.2
