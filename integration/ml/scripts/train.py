"""Train + select the complaint gate and category classifier on train/val only; export artifacts.

Usage (from repo root):  PYTHONPATH=. ml/.venv/bin/python ml/scripts/train.py
The test split is never read here.
Outputs: ml/artifacts/{gate,category}.joblib, ml/artifacts/manifest.json, ml/results/experiment_register.csv
"""
import datetime as dt
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

from ml.src.models import SEED, build, ece, scores

ML = Path(__file__).resolve().parents[1]
CATS = ["AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER"]
MODEL_VERSION = "tfidf-baseline-v1"
PRECISION_TARGET = 0.90

VARIANTS = ["P0", "P1"]
FEATS = ["word11", "word12", "char25", "word12+char25"]
MIN_DF = [1, 2]
CS = [0.1, 1.0, 10.0]
CWS = [None, "balanced"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    lab = pd.read_parquet(ML / "data" / "annotation" / "labels.parquet")
    split = pd.read_csv(ML / "data" / "splits" / "split_manifest.csv")[["ann_id", "split"]]
    df = lab.merge(split, on="ann_id", how="inner", validate="1:1")
    assert len(df) == len(lab)
    return df[df.split != "test"].copy()   # test is never touched in this script


def run_grid(task, Xtr, ytr, Xva, yva, labels, learners, register):
    n_min = int(pd.Series(ytr).value_counts().min())
    configs = [("P1", "-", 0, "dummy", None, None)]
    for v, f, m, ln, C, cw in itertools.product(VARIANTS, FEATS, MIN_DF, learners, CS, CWS):
        configs.append((v, f, m, ln, C, cw))
    results = []
    for k, (v, f, m, ln, C, cw) in enumerate(configs):
        pipe = build(v, f, m, ln, C=C or 1.0, class_weight=cw, n_min_class=n_min)
        t0 = time.perf_counter()
        pipe.fit(Xtr, ytr)
        fit_s = time.perf_counter() - t0
        s = scores(yva, pipe.predict(Xva), labels)
        row = {"experiment_id": f"{task}-{k:03d}", "task": task, "preprocessing_variant": v, "feature_type": f,
               "min_df": m, "learner": ln, "C": C, "class_weight": cw or "none", "random_seed": SEED,
               "training_time_s": round(fit_s, 3), "val_macro_F1": round(s["macro_f1"], 4),
               "val_min_recall": round(min(s["recall"].values()), 4),
               "val_per_class_recall": json.dumps({a: round(b, 3) for a, b in s["recall"].items()})}
        register.append(row)
        results.append((row, pipe))
    best_row, best_pipe = max(
        (r for r in results if r[0]["learner"] != "dummy"),
        key=lambda r: (r[0]["val_macro_F1"], r[0]["val_min_recall"], -r[0]["training_time_s"]))
    dummy_row = results[0][0]
    return best_row, best_pipe, dummy_row


def gate_band(p, y):
    """Smallest symmetric band around 0.5 such that decisions outside it reach PRECISION_TARGET accuracy."""
    for d in np.arange(0.0, 0.5, 0.025):
        lo, hi = 0.5 - d, 0.5 + d
        auto = (p < lo) | (p >= hi)
        if auto.sum() >= 20 and ((p[auto] >= 0.5) == y[auto]).mean() >= PRECISION_TARGET:
            return float(round(lo, 3)), float(round(hi, 3)), float(auto.mean())
    return 0.0, 1.01, 0.0     # target unreachable -> every gate decision is flagged for review


def category_threshold(conf, correct):
    for t in np.arange(0.0, 1.0, 0.025):
        auto = conf >= t
        if auto.sum() >= 15 and correct[auto].mean() >= PRECISION_TARGET:
            return float(round(t, 3)), float(auto.mean())
    return 1.01, 0.0


def main() -> int:
    df = load()
    tr, va = df[df.split == "train"], df[df.split == "val"]
    register = []

    # ---- complaint gate (unclear excluded) ----
    g_tr, g_va = tr[tr.is_complaint != "unclear"], va[va.is_complaint != "unclear"]
    ytr_g, yva_g = (g_tr.is_complaint == "yes").astype(int).values, (g_va.is_complaint == "yes").astype(int).values
    g_row, gate, g_dummy = run_grid("gate", g_tr.review.tolist(), ytr_g, g_va.review.tolist(), yva_g, [0, 1], ["lr"], register)

    # ---- category classifier (complaints only) ----
    c_tr, c_va = tr[tr.is_complaint == "yes"], va[va.is_complaint == "yes"]
    labels = [c for c in CATS if c in set(c_tr.category)]
    c_row, cat, c_dummy = run_grid("category", c_tr.review.tolist(), c_tr.category.to_numpy(dtype=str),
                                   c_va.review.tolist(), c_va.category.to_numpy(dtype=str), labels, ["lr_cal", "svc"], register)

    # ---- thresholds + calibration on validation ----
    pg = gate.predict_proba(g_va.review.tolist())[:, list(gate.classes_).index(1)]
    lo, hi, g_cov = gate_band(pg, yva_g)
    pc = cat.predict_proba(c_va.review.tolist())
    conf = pc.max(1)
    correct = (cat.classes_[pc.argmax(1)] == c_va.category.to_numpy(dtype=str))
    t_cat, c_cov = category_threshold(conf, correct)
    calib = {
        "gate_brier_val": float(brier_score_loss(yva_g, pg)),
        "gate_ece_val": ece(np.maximum(pg, 1 - pg), ((pg >= 0.5) == yva_g).astype(float)),
        "category_ece_val": ece(conf, correct.astype(float)),
        "gate_auto_coverage_val": g_cov,
        "category_auto_coverage_val": c_cov,
    }

    art = ML / "artifacts"
    art.mkdir(exist_ok=True)
    joblib.dump(gate, art / "gate.joblib")
    joblib.dump(cat, art / "category.joblib")
    split_info = json.loads((ML / "data" / "splits" / "split_info.json").read_text())
    manifest = {
        "model_version": MODEL_VERSION,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "files": {"gate": "gate.joblib", "category": "category.joblib"},
        "categories": [str(c) for c in cat.classes_],
        "thresholds": {"gate_decision": 0.5, "gate_review_low": lo, "gate_review_high": hi,
                       "category_review": t_cat, "precision_target": PRECISION_TARGET},
        "score_semantics": {
            "complaint_score": "P(technical complaint) from the logistic-regression gate (raw predict_proba)",
            "category_score": "top-class probability of the sigmoid-calibrated category model (CalibratedClassifierCV over LR or LinearSVC, fitted on train folds)",
            "needs_review": "gate score inside [gate_review_low, gate_review_high) OR category_score < category_review; "
                            "thresholds chosen on validation to reach precision_target on automatic decisions",
        },
        "selected": {"gate": g_row, "category": c_row},
        "dummy_val": {"gate": g_dummy, "category": c_dummy},
        "calibration": calib,
        "data": {
            "labels_parquet_sha256": sha(ML / "data" / "annotation" / "labels.parquet"),
            "split_manifest_sha256": split_info["sha256"],
            "n_train_gate": int(len(g_tr)), "n_val_gate": int(len(g_va)),
            "n_train_category": int(len(c_tr)), "n_val_category": int(len(c_va)),
            "label_provenance": "AI-assisted reference labels (two independent Claude coders + adjudicator); see reports/agreement.md",
            "sources": "AURA-Sentiment + AURA-Classification v2 (MIT), see reports/data_manifest.md",
        },
        "seed": SEED,
        "sklearn_version": __import__("sklearn").__version__,
    }
    (art / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    (ML / "results").mkdir(exist_ok=True)
    pd.DataFrame(register).assign(split_manifest_hash=split_info["sha256"],
                                  dataset_version=manifest["data"]["labels_parquet_sha256"][:12]) \
        .to_csv(ML / "results" / "experiment_register.csv", index=False)
    print(json.dumps({"gate": g_row, "gate_dummy": g_dummy, "category": c_row, "category_dummy": c_dummy,
                      "thresholds": manifest["thresholds"], "calibration": calib}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
