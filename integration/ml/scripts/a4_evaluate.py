"""A4 one-time evaluation on the frozen holdout, after results/a4/selection.json is committed.

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_evaluate.py
Evaluates every candidate with the thresholds chosen on validation (baseline-v1: its own deployed thresholds),
on: holdout (all), holdout random stratum (representative), holdout enriched strata, code-switch subset,
and v1_test (secondary, NOT blind). Also: paired bootstrap vs baseline, latency/size/memory of the exported model,
and the external AURA-Classification human proxy for the gate.
Later runs = reproduction check against results/a4/holdout_metrics.json.
"""
import json
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.src.a4_common import (CATS, LABELS7, bootstrap_ci, decisions, load_a4, metrics, paired_bootstrap_delta,
                              review_stats)

ML = Path(__file__).resolve().parents[1]
RES = ML / "results/a4"


def committed(path: Path) -> bool:
    r = subprocess.run(["git", "status", "--porcelain", str(path)], cwd=ML, capture_output=True, text=True)
    t = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ML, capture_output=True, text=True)
    return r.stdout.strip() == "" and t.returncode == 0


def two_stage(dirpath, texts):
    gate, cat = joblib.load(dirpath / "gate.joblib"), joblib.load(dirpath / "category.joblib")
    pg = gate.predict_proba(texts)[:, list(gate.classes_).index(1)]
    pc = cat.predict_proba(texts)
    P = np.zeros((len(texts), 7))
    P[:, 0] = 1 - pg
    for j, c in enumerate(cat.classes_):
        P[:, LABELS7.index(c)] = pg * pc[:, j]
    return P


def probs_for(name, run, texts):
    if name == "E0_baseline_v1":
        return two_stage(ML / "artifacts/baseline-v1", texts)
    if name.startswith("E1") or name.startswith("E2"):
        return two_stage(ML / "artifacts/a4" / run, texts)
    if name.startswith("E3") or name.startswith("E4"):
        from ml.src.hf_model import HFPredictor
        return HFPredictor(ML / "artifacts/a4" / run).predict_proba(texts)
    if name.startswith("E5"):
        sys.path.insert(0, str(ML / "scripts"))
        from a4_experiments import e5_embed
        head = joblib.load(ML / "artifacts/a4/E5_e5_lr/head.joblib")
        P = np.zeros((len(texts), 7))
        P[:, [LABELS7.index(c) for c in head.classes_]] = head.predict_proba(e5_embed(texts))
        return P
    raise ValueError(name)


def main() -> int:
    sel_path = RES / "selection.json"
    if not sel_path.exists() or not committed(sel_path):
        print("results/a4/selection.json must exist and be committed before the holdout is evaluated.")
        return 1
    sel = json.loads(sel_path.read_text())
    lab = load_a4()
    hold = lab[(lab.a4_split == "holdout") & (lab.label_final != "UNCLEAR")].reset_index(drop=True)
    v1t = lab[(lab.a4_split == "v1_test") & (lab.label_final != "UNCLEAR")].reset_index(drop=True)
    base_th = json.loads((ML / "artifacts/baseline-v1/manifest.json").read_text())["thresholds"]
    subsets = {"holdout_all": np.ones(len(hold), bool), "holdout_random": (hold.stratum == "random").values,
               "holdout_enriched": (hold.stratum != "random").values,
               "holdout_codeswitch": hold.text_p0.map(lambda t: len([w for w in re.findall(r"[A-Za-z]{2,}", t)
                                                                      if w.lower() not in {"url", "email", "phone", "num", "user"}]) >= 1).values}
    out = {"selected": sel["selected"], "model_version": sel["model_version"], "label_note":
           "Reference labels are AI-assisted (sonnet+fable coders, opus adjudicator), NOT independent human ground truth.",
           "holdout_n_excl_unclear": int(len(hold)), "candidates": {}}
    probs = {}
    for name, c in sel["candidates"].items():
        th = base_th if name == "E0_baseline_v1" else c["thresholds"]
        P = probs_for(name, c["artifact_run"], hold.review.tolist())
        probs[name] = P
        r = {"thresholds": th}
        for sname, mask in subsets.items():
            if mask.sum() == 0:
                continue
            m = metrics(P[mask], hold.label_final.values[mask])
            m["review"] = review_stats(P[mask], hold.label_final.values[mask], th)
            r[sname] = m
        Pv = probs_for(name, c["artifact_run"], v1t.review.tolist())
        r["v1_test_NOT_BLIND"] = {k: v for k, v in metrics(Pv, v1t.label_final.values).items() if not k.startswith("per_class")}
        out["candidates"][name] = r
        print(name, "holdout e2e", r["holdout_all"]["e2e_macro_f1"], "gate", r["holdout_all"]["gate_macro_f1"],
              "cat", r["holdout_all"]["category_macro_f1"], "TRANS", r["holdout_all"]["recall_TRANS"], "UX", r["holdout_all"]["recall_UX"])

    y = hold.label_final.values
    s, b = sel["selected"], "E0_baseline_v1"
    ci = {}
    for key in ["e2e_macro_f1", "gate_macro_f1", "category_macro_f1"]:
        ci[key] = {"selected": bootstrap_ci(probs[s], y, key), "baseline": bootstrap_ci(probs[b], y, key),
                   "delta_selected_minus_baseline": paired_bootstrap_delta(probs[s], probs[b], y, key)}
    out["ci95_holdout_all"] = ci
    # confusion matrices (e2e, holdout_all) for selected and baseline
    from sklearn.metrics import confusion_matrix
    for name in {s, b}:
        joint = decisions(probs[name])[4]
        cm = confusion_matrix(y, joint, labels=LABELS7)
        pd.DataFrame(cm, index=LABELS7, columns=LABELS7).to_csv(RES / f"confusion_holdout_{name}.csv")
    errs = hold.assign(pred=decisions(probs[s])[4])[lambda d: d.pred != d.label_final]
    errs[["item_id", "stratum", "label_final", "pred", "uncertain", "adjudicated", "text_p0"]].to_csv(RES / "errors_holdout_selected.csv", index=False)

    # external human proxy: AURA-Cls records in groups never used in A4 train/val
    corpus = pd.read_parquet(ML / "data/interim/corpus.parquet")
    used = set(lab.dup_group[lab.a4_split.isin(["train", "val"])])
    ext = corpus[(corpus.source == "aura_classification_v2") & ~corpus.dup_group.isin(used) & corpus.exclusion_reason.isna()].drop_duplicates("dup_group")
    from sklearn.metrics import cohen_kappa_score, precision_recall_fscore_support
    ref = (ext.aura_label == "bug_report").to_numpy(dtype=bool)
    out["external_aura_proxy"] = {}
    for name in {s, b}:
        pc = decisions(probs_for(name, sel["candidates"][name]["artifact_run"], ext.review.tolist()))[1]
        P_, R_, F_, _ = precision_recall_fscore_support(ref, pc, average="binary", zero_division=0)
        out["external_aura_proxy"][name] = {"n": int(len(ext)), "agreement": round(float((ref == pc).mean()), 4),
                                            "kappa": round(float(cohen_kappa_score(ref, pc)), 4),
                                            "precision_vs_bug_report": round(float(P_), 4), "recall_vs_bug_report": round(float(R_), 4)}

    # cost of the exported selected model through the real contract
    exp = ML / sel["export_dir"]
    size_mb = sum(f.stat().st_size for f in exp.rglob("*") if f.is_file()) / 1e6
    code = (f"import os,time,resource,json;os.environ['ML_ARTIFACT_DIR']=r'{exp}';"
            "from ml.infer import predict_text;import pandas as pd;"
            f"t=pd.read_parquet(r'{ML / 'data/a4/labels_a4.parquet'}');t=t[t.set=='holdout'].review.tolist()[:200];"
            "t0=time.perf_counter();predict_text(t[0]);load=time.perf_counter()-t0;t1=time.perf_counter();[predict_text(x) for x in t[1:]];"
            "lat=(time.perf_counter()-t1)/(len(t)-1);print(json.dumps({'first_call_s':round(load,2),'latency_ms':round(lat*1000,2),"
            "'peak_rss_mb':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6,1)}))")
    r = subprocess.run([sys.executable, "-c", code], cwd=ML.parent, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(ML.parent)})
    cost = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {"error": r.stderr[-500:]}
    out["cost_selected_export"] = {"artifact_size_mb": round(size_mb, 1), **cost, "device": "CPU (Apple M2 Max)"}
    out["latency_note"] = "latency measured through ml.infer.predict_text, one message at a time"

    path = RES / "holdout_metrics.json"
    if path.exists():
        old = json.loads(path.read_text())
        keys = [k for k in out if k not in ("cost_selected_export",)]
        same = all(json.dumps(old.get(k), sort_keys=True) == json.dumps(out[k], sort_keys=True) for k in keys)
        print("REPRODUCTION CHECK:", "identical metrics" if same else "METRICS DIFFER")
        return 0 if same else 1
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: out[k] for k in ("ci95_holdout_all", "external_aura_proxy", "cost_selected_export")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
