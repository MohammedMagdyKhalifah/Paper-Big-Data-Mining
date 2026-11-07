"""A4 shared definitions: 7-way label space, data loading, unified metrics, review thresholds.

Every candidate model is reduced to a 7-column probability matrix P over LABELS7 = [NO, six categories]:
  complaint_score = 1 - P[NO];  is_complaint = complaint_score >= 0.5
  category = argmax over the six category columns;  category_score = P[cat] / complaint_score
Two-stage TF-IDF models map to this space as P[NO] = 1 - p_gate, P[c] = p_gate * p(c | complaint).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_recall_fscore_support

ML = Path(__file__).resolve().parents[1]
CATS = ["AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER"]
LABELS7 = ["NO"] + CATS
PRECISION_TARGET = 0.90


def load_a4(require_split: bool = True) -> pd.DataFrame:
    lab = pd.read_parquet(ML / "data/a4/labels_a4.parquet")
    if require_split:
        sp = pd.read_csv(ML / "data/a4/split_a4.csv")[["item_id", "a4_split"]]
        lab = lab.merge(sp, on="item_id", how="left", validate="1:1")
    return lab


def decisions(P: np.ndarray):
    P = np.asarray(P, dtype=float)
    cs = 1.0 - P[:, 0]
    is_c = cs >= 0.5
    cat_idx = P[:, 1:].argmax(1)
    cat = np.array(CATS)[cat_idx]
    cat_score = np.where(cs > 0, P[np.arange(len(P)), cat_idx + 1] / np.maximum(cs, 1e-12), 0.0)
    joint = np.where(is_c, cat, "NO")
    return cs, is_c, cat, cat_score, joint


def per_class(y, p, labels):
    P, R, F, S = precision_recall_fscore_support(y, p, labels=labels, zero_division=0)
    return {l: {"precision": round(float(a), 4), "recall": round(float(b), 4), "f1": round(float(c), 4), "support": int(d)}
            for l, a, b, c, d in zip(labels, P, R, F, S)}


def macro(y, p, labels):
    return float(f1_score(y, p, labels=labels, average="macro", zero_division=0))


def metrics(P, y_joint):
    """y_joint: reference labels in LABELS7 (UNCLEAR must already be removed)."""
    y = np.asarray(y_joint, dtype=str)
    cs, is_c, cat, cat_score, joint = decisions(P)
    yc = y != "NO"
    out = {
        "n": int(len(y)),
        "e2e_macro_f1": round(macro(y, joint, LABELS7), 4),
        "gate_macro_f1": round(macro(yc.astype(int), is_c.astype(int), [0, 1]), 4),
        "category_macro_f1": round(macro(y[yc], cat[yc], CATS), 4) if yc.any() else None,
        "e2e_accuracy": round(float((joint == y).mean()), 4),
        "per_class_e2e": per_class(y, joint, LABELS7),
        "per_class_category": per_class(y[yc], cat[yc], CATS) if yc.any() else None,
    }
    out["recall_TRANS"] = out["per_class_category"]["TRANS"]["recall"] if yc.any() else None
    out["recall_UX"] = out["per_class_category"]["UX"]["recall"] if yc.any() else None
    return out


def choose_thresholds(P, y_joint):
    """Same rule as v1: smallest gate band around 0.5 / lowest category threshold giving ~90% precision of
    automatic decisions on validation."""
    y = np.asarray(y_joint, dtype=str)
    cs, is_c, cat, cat_score, joint = decisions(P)
    yc = y != "NO"
    band = (0.0, 1.01)
    for d in np.arange(0.0, 0.5, 0.025):
        lo, hi = 0.5 - d, 0.5 + d
        auto = (cs < lo) | (cs >= hi)
        if auto.sum() >= 20 and (is_c[auto] == yc[auto]).mean() >= PRECISION_TARGET:
            band = (round(float(lo), 3), round(float(hi), 3))
            break
    t_cat = 1.01
    m = yc & is_c
    for t in np.arange(0.0, 1.0, 0.025):
        auto = m & (cat_score >= t)
        if auto.sum() >= 15 and (cat[auto] == y[auto]).mean() >= PRECISION_TARGET:
            t_cat = round(float(t), 3)
            break
    return {"gate_review_low": band[0], "gate_review_high": band[1], "category_review": t_cat}


def review_stats(P, y_joint, th):
    """Abstention rate and precision/coverage of automatically accepted end-to-end decisions."""
    y = np.asarray(y_joint, dtype=str)
    cs, is_c, cat, cat_score, joint = decisions(P)
    flag = ((cs >= th["gate_review_low"]) & (cs < th["gate_review_high"])) | (is_c & (cat_score < th["category_review"]))
    auto = ~flag
    return {"review_rate": round(float(flag.mean()), 4), "auto_coverage": round(float(auto.mean()), 4),
            "auto_accuracy": round(float((joint[auto] == y[auto]).mean()), 4) if auto.any() else None,
            "auto_complaint_coverage": round(float((auto & is_c).sum() / max(is_c.sum(), 1)), 4)}


def ece(conf, correct, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            tot += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(tot)


def bootstrap_ci(P, y_joint, key, n_boot=2000, seed=42, groups=None):
    """Percentile 95% CI of a metric from `metrics`, resampling items (each item is its own dup group)."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y_joint, dtype=str)
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        vals.append(metrics(P[i], y[i])[key])
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def paired_bootstrap_delta(P1, P2, y_joint, key, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    y = np.asarray(y_joint, dtype=str)
    d = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        d.append(metrics(P1[i], y[i])[key] - metrics(P2[i], y[i])[key])
    return [round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]
