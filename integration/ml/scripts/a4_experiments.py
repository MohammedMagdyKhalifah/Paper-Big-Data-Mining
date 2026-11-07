"""A4 controlled experiments on A4 train / val only (the holdout and v1_test are never read here).

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_experiments.py <cmd>
  baseline        E0: score the frozen tfidf-baseline-v1 artifact on A4 val
  tfidf           E1: v1 two-stage architecture re-tuned on A4 data       (+ --synthetic for E2)
  marbert_grid    E3: lr x loss grid, seed 42
  marbert_seeds   E3: best grid config with seeds 42, 13, 7              (+ --synthetic for E4)
  e5              E5: multilingual-e5-base embeddings + LogisticRegression
Every run writes results/a4/runs/<run_id>/{config.json, metrics_val.json, val_probs.npy[, history.json]}.
Models selected for export are saved to artifacts/a4/<run_id>/ (transformer runs are saved, others deleted later
by scripts/a4_select.py to respect disk space).
"""
import itertools
import json
import os
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.src.a4_common import CATS, LABELS7, decisions, load_a4, metrics
from ml.src.models import build

ML = Path(__file__).resolve().parents[1]
RUNS = ML / "results/a4/runs"
ART = ML / "artifacts/a4"


def data(synthetic=False):
    lab = load_a4()
    lab = lab[lab.label_final != "UNCLEAR"]
    tr = lab[lab.a4_split == "train"]
    if synthetic:
        tr = pd.concat([tr, lab[lab.a4_split == "train_synthetic"]])
    va = lab[lab.a4_split == "val"]
    return tr, va


def save_run(run_id, cfg, P_val, y_val, extra=None):
    d = RUNS / run_id
    d.mkdir(parents=True, exist_ok=True)
    m = metrics(P_val, y_val)
    (d / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    (d / "metrics_val.json").write_text(json.dumps({**m, **(extra or {})}, indent=2, ensure_ascii=False))
    np.save(d / "val_probs.npy", P_val.astype(np.float32))
    print(run_id, "val e2e", m["e2e_macro_f1"], "gate", m["gate_macro_f1"], "cat", m["category_macro_f1"],
          "TRANS rec", m["recall_TRANS"], "UX rec", m["recall_UX"])
    return m


def two_stage_probs(gate, cat, texts):
    pg = gate.predict_proba(texts)[:, list(gate.classes_).index(1)]
    pc = cat.predict_proba(texts)
    P = np.zeros((len(texts), 7))
    P[:, 0] = 1 - pg
    for j, c in enumerate(cat.classes_):
        P[:, LABELS7.index(c)] = pg * pc[:, j]
    return P


def cmd_baseline():
    _, va = data()
    gate = joblib.load(ML / "artifacts/baseline-v1/gate.joblib")
    cat = joblib.load(ML / "artifacts/baseline-v1/category.joblib")
    P = two_stage_probs(gate, cat, va.review.tolist())
    save_run("E0_baseline_v1", {"model": "tfidf-baseline-v1 (frozen artifact)"}, P, va.label_final.values)


def cmd_tfidf(synthetic=False):
    tr, va = data(synthetic)
    grid = list(itertools.product(["P0", "P1"], ["char25", "word12+char25"], [1, 2], [1.0, 10.0], ["balanced"]))
    # gate: selected by val gate macro-F1 (v1 procedure)
    ytr_g = (tr.label_final != "NO").astype(int).values
    yva_g = (va.label_final != "NO").astype(int).values
    from sklearn.metrics import f1_score
    best_g = None
    for v, f, m, C, cw in grid:
        p = build(v, f, m, "lr", C=C, class_weight=cw).fit(tr.review.tolist(), ytr_g)
        s = f1_score(yva_g, p.predict(va.review.tolist()), average="macro")
        if best_g is None or s > best_g[0]:
            best_g = (s, (v, f, m, C, cw), p)
    trc, vac = tr[tr.label_final != "NO"], va[va.label_final != "NO"]
    n_min = int(trc.label_final.value_counts().min())
    best_c = None
    for (v, f, m, C, cw), ln in itertools.product(grid, ["lr_cal", "svc"]):
        p = build(v, f, m, ln, C=C, class_weight=cw, n_min_class=n_min).fit(trc.review.tolist(), trc.label_final.to_numpy(dtype=str))
        s = f1_score(vac.label_final.to_numpy(dtype=str), p.predict(vac.review.tolist()), labels=CATS, average="macro", zero_division=0)
        if best_c is None or s > best_c[0]:
            best_c = (s, (v, f, m, C, cw, ln), p)
    P = two_stage_probs(best_g[2], best_c[2], va.review.tolist())
    run = "E2_tfidf_a4_synth" if synthetic else "E1_tfidf_a4"
    cfg = {"gate": dict(zip(["variant", "features", "min_df", "C", "class_weight"], best_g[1])),
           "category": dict(zip(["variant", "features", "min_df", "C", "class_weight", "learner"], best_c[1])),
           "n_train": int(len(tr)), "synthetic": synthetic}
    save_run(run, cfg, P, va.label_final.values, {"val_gate_stage_macro_f1": round(best_g[0], 4), "val_category_stage_macro_f1": round(best_c[0], 4)})
    d = ART / run
    d.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_g[2], d / "gate.joblib")
    joblib.dump(best_c[2], d / "category.joblib")


MARBERT_BASE = {"max_len": 128, "batch_size": 16, "grad_accum": 2, "max_epochs": 6, "patience": 2}


def run_marbert(run_id, cfg, synthetic=False, keep_model=True):
    from ml.src.hf_model import fit_temperature, softmax, train_marbert
    import torch
    tr, va = data(synthetic)
    t0 = time.time()
    torch.mps.reset_peak_memory_stats() if hasattr(torch.mps, "reset_peak_memory_stats") else None
    model, tok, hist, vl = train_marbert(tr.review.tolist(), tr.label_final.tolist(), va.review.tolist(), va.label_final.tolist(), cfg)
    y_idx = np.array([LABELS7.index(l) for l in va.label_final])
    T = fit_temperature(vl, y_idx)
    P = softmax(vl, T)
    extra = {"temperature": T, "train_minutes": round((time.time() - t0) / 60, 2), "best_epoch": int(np.argmax([h["val_e2e_macro_f1"] for h in hist]) + 1),
             "mps_driver_mem_gb_end": round(torch.mps.driver_allocated_memory() / 1e9, 2) if torch.backends.mps.is_available() else None}
    d = RUNS / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "history.json").write_text(json.dumps(hist, indent=2))
    np.save(d / "val_logits.npy", vl)
    m = save_run(run_id, {**cfg, "model": "UBC-NLP/MARBERTv2@fe88db9", "synthetic": synthetic, "n_train": int(len(tr))}, P, va.label_final.values, extra)
    if keep_model:
        out = ART / run_id
        out.mkdir(parents=True, exist_ok=True)
        model.half().save_pretrained(out, safe_serialization=True)   # fp16 on disk (disk budget); loaded back as fp32
        tok.save_pretrained(out)
        (out / "a4_meta.json").write_text(json.dumps({"temperature": T, "max_len": cfg["max_len"], "labels": LABELS7, "run_id": run_id}))
    del model
    return m


def cmd_marbert_grid():
    for lr, loss in itertools.product([2e-5, 4e-5], ["ce", "ce_sqrt_class_weights"]):
        rid = f"E3_marbert_lr{lr:g}_{loss}_s42"
        if (RUNS / rid / "metrics_val.json").exists():
            print("skip existing", rid)
            continue
        run_marbert(rid, {**MARBERT_BASE, "lr": lr, "loss": loss, "seed": 42}, keep_model=False)


def best_grid_cfg():
    rows = []
    for d in RUNS.glob("E3_marbert_lr*_s42"):
        c = json.loads((d / "config.json").read_text())
        m = json.loads((d / "metrics_val.json").read_text())
        rows.append((m["e2e_macro_f1"], c))
    return max(rows, key=lambda r: r[0])[1]


def cmd_marbert_seeds(synthetic=False):
    c = best_grid_cfg()
    base = {k: c[k] for k in ["max_len", "batch_size", "grad_accum", "max_epochs", "patience", "lr", "loss"]}
    seeds = [int(x) for x in sys.argv[sys.argv.index('--seeds') + 1].split(',')] if '--seeds' in sys.argv else [42, 13, 7]
    for s in seeds:
        rid = f"{'E4_marbert_synth' if synthetic else 'E3_marbert_final'}_s{s}"
        if (RUNS / rid / "metrics_val.json").exists():
            print("skip existing", rid)
            continue
        run_marbert(rid, {**base, "seed": s}, synthetic=synthetic, keep_model=True)


def e5_embed(texts, bs=64):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch
    from transformers import AutoModel, AutoTokenizer
    from ml.src.text import p0
    rev = "d128750597153bb5987e10b1c3493a34e5a4502a"
    tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-base", revision=rev)
    mod = AutoModel.from_pretrained("intfloat/multilingual-e5-base", revision=rev).to("mps").eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), bs):
            enc = tok(["query: " + p0(t) for t in texts[i:i + bs]], padding=True, truncation=True, max_length=128, return_tensors="pt").to("mps")
            h = mod(**enc).last_hidden_state
            m = enc["attention_mask"].unsqueeze(-1).float()
            e = (h * m).sum(1) / m.sum(1)
            out.append(torch.nn.functional.normalize(e, dim=-1).cpu().numpy())
    return np.concatenate(out)


def cmd_e5():
    from sklearn.linear_model import LogisticRegression
    tr, va = data()
    Xtr, Xva = e5_embed(tr.review.tolist()), e5_embed(va.review.tolist())
    best = None
    for C, cw in itertools.product([0.3, 1, 3, 10, 30], [None, "balanced"]):
        clf = LogisticRegression(C=C, class_weight=cw, max_iter=5000).fit(Xtr, tr.label_final.to_numpy(dtype=str))
        P = np.zeros((len(va), 7))
        P[:, [LABELS7.index(c) for c in clf.classes_]] = clf.predict_proba(Xva)
        s = metrics(P, va.label_final.values)["e2e_macro_f1"]
        if best is None or s > best[0]:
            best = (s, C, cw, clf, P)
    save_run("E5_e5_lr", {"model": "intfloat/multilingual-e5-base@d128750 (frozen) + LogisticRegression", "C": best[1],
                          "class_weight": best[2] or "none"}, best[4], va.label_final.values)
    (ART / "E5_e5_lr").mkdir(parents=True, exist_ok=True)
    joblib.dump(best[3], ART / "E5_e5_lr" / "head.joblib")


if __name__ == "__main__":
    cmd = sys.argv[1]
    syn = "--synthetic" in sys.argv
    {"baseline": cmd_baseline, "tfidf": lambda: cmd_tfidf(syn), "marbert_grid": cmd_marbert_grid,
     "marbert_seeds": lambda: cmd_marbert_seeds(syn), "e5": cmd_e5}[cmd]()
