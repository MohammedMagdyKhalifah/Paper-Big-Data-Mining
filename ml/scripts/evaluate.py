"""One-time held-out evaluation of the frozen artifacts.

Usage (from repo root):  PYTHONPATH=. ml/.venv/bin/python ml/scripts/evaluate.py
First run writes ml/results/test_metrics.json and ml/reports/evaluation.md.
Later runs are reproduction checks: they recompute everything and report whether the numbers are identical.
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (cohen_kappa_score, confusion_matrix, f1_score, precision_recall_fscore_support)

ML = Path(__file__).resolve().parents[1]
RES = ML / "results"
SEED = 42
N_BOOT = 2000


def per_class(y, p, labels):
    P, R, F, S = precision_recall_fscore_support(y, p, labels=labels, zero_division=0)
    return {str(l): {"precision": round(float(a), 4), "recall": round(float(b), 4), "f1": round(float(c), 4),
                     "support": int(d)} for l, a, b, c, d in zip(labels, P, R, F, S)}


def macro(y, p, labels):
    return float(f1_score(y, p, labels=labels, average="macro", zero_division=0))


def boot_ci(y, p, p_base, labels, rng):
    """95% percentile CI for macro-F1 and for the difference vs baseline (each test item is its own dup group)."""
    y, p, p_base = map(np.asarray, (y, p, p_base))
    n = len(y)
    m, d = [], []
    for _ in range(N_BOOT):
        i = rng.integers(0, n, n)
        a = macro(y[i], p[i], labels)
        m.append(a)
        d.append(a - macro(y[i], p_base[i], labels))
    q = lambda v: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
    return q(m), q(d)


def plot_cm(cm, labels, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=45)
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center", color="black" if cm[i, j] < cm.max() / 2 else "white")
    ax.set_xlabel("predicted")
    ax.set_ylabel("reference label")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    rng = np.random.default_rng(SEED)
    man = json.loads((ML / "artifacts" / "manifest.json").read_text())
    gate = joblib.load(ML / "artifacts" / "gate.joblib")
    cat = joblib.load(ML / "artifacts" / "category.joblib")
    th = man["thresholds"]
    lab = pd.read_parquet(ML / "data" / "annotation" / "labels.parquet")
    split = pd.read_csv(ML / "data" / "splits" / "split_manifest.csv")[["ann_id", "split"]]
    df = lab.merge(split, on="ann_id", validate="1:1")
    tr, te = df[df.split == "train"], df[df.split == "test"]
    out = {"model_version": man["model_version"], "split_manifest_sha256": man["data"]["split_manifest_sha256"]}

    # ---------- gate ----------
    g_te = te[te.is_complaint != "unclear"]
    y_g = (g_te.is_complaint == "yes").astype(int).values
    pos = list(gate.classes_).index(1)
    p_g = gate.predict_proba(g_te.review.tolist())[:, pos]
    yhat_g = (p_g >= th["gate_decision"]).astype(int)
    d_g = DummyClassifier(strategy="most_frequent").fit(np.zeros(len(tr[tr.is_complaint != "unclear"])),
                                                         (tr[tr.is_complaint != "unclear"].is_complaint == "yes").astype(int))
    base_g = d_g.predict(np.zeros(len(y_g)))
    ci, dci = boot_ci(y_g, yhat_g, base_g, [0, 1], rng)
    auto = (p_g < th["gate_review_low"]) | (p_g >= th["gate_review_high"])
    out["gate"] = {"n_test": int(len(y_g)), "macro_f1": round(macro(y_g, yhat_g, [0, 1]), 4), "macro_f1_ci95": ci,
                   "dummy_macro_f1": round(macro(y_g, base_g, [0, 1]), 4), "delta_vs_dummy_ci95": dci,
                   "per_class": per_class(y_g, yhat_g, [0, 1]),
                   "confusion[ref x pred] (0=not,1=complaint)": confusion_matrix(y_g, yhat_g, labels=[0, 1]).tolist(),
                   "auto_coverage": round(float(auto.mean()), 4),
                   "auto_accuracy": round(float((yhat_g[auto] == y_g[auto]).mean()), 4) if auto.any() else None,
                   "n_unclear_excluded": int((te.is_complaint == "unclear").sum())}

    # ---------- category (reference complaints only) ----------
    c_te = te[te.is_complaint == "yes"]
    labels = list(cat.classes_)
    y_c = c_te.category.to_numpy(dtype=str)
    pc = cat.predict_proba(c_te.review.tolist())
    yhat_c = cat.classes_[pc.argmax(1)]
    conf = pc.max(1)
    c_tr = tr[tr.is_complaint == "yes"]
    base_c = DummyClassifier(strategy="most_frequent").fit(np.zeros(len(c_tr)), c_tr.category.to_numpy(dtype=str)).predict(np.zeros(len(y_c)))
    ci, dci = boot_ci(y_c, yhat_c, base_c, labels, rng)
    cm = confusion_matrix(y_c, yhat_c, labels=labels)
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(RES / "confusion_category_test.csv")
    plot_cm(cm, labels, RES / "confusion_category_test.png", f"Category — test (n={len(y_c)})")
    auto_c = conf >= th["category_review"]
    out["category"] = {"n_test": int(len(y_c)), "macro_f1": round(macro(y_c, yhat_c, labels), 4), "macro_f1_ci95": ci,
                       "dummy_macro_f1": round(macro(y_c, base_c, labels), 4), "delta_vs_dummy_ci95": dci,
                       "accuracy": round(float((yhat_c == y_c).mean()), 4),
                       "weighted_f1": round(float(f1_score(y_c, yhat_c, labels=labels, average="weighted", zero_division=0)), 4),
                       "per_class": per_class(y_c, yhat_c, labels), "labels": labels, "confusion": cm.tolist(),
                       "auto_coverage": round(float(auto_c.mean()), 4),
                       "auto_accuracy": round(float((yhat_c[auto_c] == y_c[auto_c]).mean()), 4) if auto_c.any() else None}
    errs = c_te.assign(pred=yhat_c, conf=conf)[lambda d: d.pred != d.category]
    errs[["ann_id", "category", "pred", "conf", "multi_issue", "uncertain", "text_p0"]].to_csv(RES / "errors_category_test.csv", index=False)

    # ---------- end-to-end: gate -> category vs reference joint label ----------
    e_te = te[te.is_complaint != "unclear"]
    from ml.infer import _reset_cache, predict_text
    _reset_cache()
    preds = [predict_text(t) for t in e_te.review]
    e_pred = [r["category"] if r["is_complaint"] else "NO" for r in preds]
    e_ref = e_te.label_final.to_numpy(dtype=str)
    e_labels = labels + ["NO"]
    out["end_to_end"] = {"n_test": int(len(e_ref)), "macro_f1": round(macro(e_ref, e_pred, e_labels), 4),
                         "accuracy": round(float((np.array(e_pred) == e_ref).mean()), 4),
                         "per_class": per_class(e_ref, e_pred, e_labels),
                         "needs_review_rate": round(float(np.mean([r["needs_review"] for r in preds])), 4)}
    nr = np.array([r["needs_review"] for r in preds])
    if (~nr).any():
        out["end_to_end"]["accuracy_when_not_flagged"] = round(float((np.array(e_pred)[~nr] == e_ref[~nr]).mean()), 4)

    # ---------- external proxy: AURA-Classification v2 human labels ----------
    corpus = pd.read_parquet(ML / "data" / "interim" / "corpus.parquet")
    seen = set(df[df.split.isin(["train", "val"])].dup_group)
    ext = corpus[(corpus.source == "aura_classification_v2") & ~corpus.dup_group.isin(seen) & corpus.exclusion_reason.isna()]
    ext = ext.drop_duplicates("dup_group")   # one item per group to avoid double counting
    p_ext = gate.predict_proba(ext.review.tolist())[:, pos] >= th["gate_decision"]
    ref_ext = (ext.aura_label == "bug_report").to_numpy(dtype=bool)
    def ext_stats(mask):
        y, p = ref_ext[mask], p_ext[mask]
        P, R, F, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0)
        return {"n": int(mask.sum()), "agreement": round(float((y == p).mean()), 4), "kappa": round(float(cohen_kappa_score(y, p)), 4),
                "precision_vs_bug_report": round(float(P), 4), "recall_vs_bug_report": round(float(R), 4), "f1": round(float(F), 4),
                "predicted_complaint_rate_by_aura_label": pd.Series(p).groupby(ext.aura_label.values[mask]).mean().round(4).to_dict()}
    out["external_aura_proxy"] = {"all_domains": ext_stats(np.ones(len(ext), bool)),
                                  "non_game": ext_stats((ext.domain != "games").values)}

    # ---------- latency ----------
    texts = te.review.tolist()[:200]
    t0 = time.perf_counter()
    for t in texts:
        predict_text(t)
    out["latency_ms_per_message_mean"] = round((time.perf_counter() - t0) / len(texts) * 1000, 3)

    path = RES / "test_metrics.json"
    if path.exists():
        old = json.loads(path.read_text())
        old.pop("latency_ms_per_message_mean", None)
        new = {k: v for k, v in out.items() if k != "latency_ms_per_message_mean"}
        same = json.dumps(old, sort_keys=True) == json.dumps(new, sort_keys=True)
        print("REPRODUCTION CHECK:", "identical metrics" if same else "METRICS DIFFER from results/test_metrics.json")
        return 0 if same else 1
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
