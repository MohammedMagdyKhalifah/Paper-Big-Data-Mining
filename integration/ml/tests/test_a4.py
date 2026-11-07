"""A4 integrity tests: frozen holdout, leakage, provenance, v1 test untouched, contract for exported A4 models."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

import ml.infer as infer

ML = Path(__file__).resolve().parents[1]
A4 = ML / "data/a4"
HOLDOUT_SHA = "65fb9459108967c211e1fec0a4caa19b1629cc6368f5f34055670f4cc8bd07f5"
KEYS = {"is_complaint", "complaint_score", "category", "category_score", "needs_review", "model_version"}

needs_labels = pytest.mark.skipif(not (A4 / "labels_a4.parquet").exists(), reason="A4 labels not built")
needs_split = pytest.mark.skipif(not (A4 / "split_a4.csv").exists(), reason="A4 split not built")


def test_holdout_frozen():
    h = pd.read_parquet(A4 / "holdout_sample.parquet")
    assert hashlib.sha256("\n".join(sorted(h.record_id)).encode()).hexdigest() == HOLDOUT_SHA
    assert len(h) == 1240 and h.dup_group.is_unique


def test_holdout_disjoint_from_training_samples():
    h = pd.read_parquet(A4 / "holdout_sample.parquet")
    t = pd.read_parquet(A4 / "train_expansion_sample.parquet")
    v1 = pd.read_parquet(ML / "data/annotation/sample.parquet")
    assert not set(h.dup_group) & set(t.dup_group)
    assert not set(h.dup_group) & set(v1.dup_group)


@needs_labels
def test_provenance_complete():
    lab = pd.read_parquet(A4 / "labels_a4.parquet")
    real = lab[lab.set != "synthetic"]
    for col in ["label_final", "coder_a_model", "coder_b_model", "adjudicator_model", "guide_version"]:
        assert real[col].notna().all(), col
    assert lab.item_id.is_unique
    changed = lab[lab.modified_in_a4 == True]  # noqa: E712
    assert changed.modification_reason.notna().all()
    assert (changed.label_v1 != changed.label_final).all()


@needs_labels
def test_v1_test_labels_untouched():
    lab = pd.read_parquet(A4 / "labels_a4.parquet")
    v1 = pd.read_parquet(ML / "data/annotation/labels.parquet").set_index("ann_id")
    t = lab[lab.set == "v1_test"].set_index("item_id")
    assert (t.label_final == v1.loc[t.index, "label_final"]).all()
    assert not t.rereview_flagged.any()


@needs_split
def test_a4_split_leakage():
    sp = pd.read_csv(A4 / "split_a4.csv")
    groups = {s: set(sp.dup_group[sp.a4_split == s]) for s in sp.a4_split.unique()}
    names = [s for s in ["train", "val", "holdout", "v1_test", "train_synthetic"] if s in groups]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not groups[a] & groups[b], (a, b)
    assert (sp.a4_split[sp.set == "holdout"] == "holdout").all()
    assert (sp.a4_split[sp.set == "v1_test"] == "v1_test").all()
    assert sp.a4_split[sp.set == "synthetic"].isin(["train_synthetic", "excluded"]).all()


def _exports():
    d = ML / "artifacts/a4/export"
    return sorted(p for p in d.iterdir() if (p / "manifest.json").exists()) if d.exists() else []


@pytest.mark.skipif(not _exports(), reason="no A4 export yet")
@pytest.mark.parametrize("exp", _exports() or [None])
def test_a4_export_contract(exp, monkeypatch):
    monkeypatch.setenv("ML_ARTIFACT_DIR", str(exp))
    infer._reset_cache()
    try:
        for t in ["رمز التحقق لا يصل عند تسجيل الدخول", "تطبيق رائع وسهل الاستخدام شكرا لكم", "الـ OTP ما يوصلني when I try to login"]:
            r = infer.predict_text(t)
            assert set(r) == KEYS and isinstance(r["is_complaint"], bool) and isinstance(r["needs_review"], bool)
            assert r["category"] is None or r["category"] in infer.CATEGORIES
            if not r["is_complaint"]:
                assert r["category"] is None and r["category_score"] is None
            for k in ("complaint_score", "category_score"):
                assert r[k] is None or 0.0 <= r[k] <= 1.0
        assert infer.predict_text("التطبيق بطيء")["model_version"] == json.loads((exp / "manifest.json").read_text())["model_version"]
        with pytest.raises(ValueError):
            infer.predict_text("  ")
    finally:
        infer._reset_cache()


def test_default_artifacts_still_baseline(monkeypatch):
    monkeypatch.delenv("ML_ARTIFACT_DIR", raising=False)
    infer._reset_cache()
    try:
        assert infer.predict_text("التطبيق بطيء")["model_version"] == "tfidf-baseline-v1"
    finally:
        infer._reset_cache()
