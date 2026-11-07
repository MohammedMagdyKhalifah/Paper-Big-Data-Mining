"""Apply the pre-registered selection rule (configs/a4_selection_rule.yaml) using VALIDATION evidence only,
choose thresholds on validation, and export the selected model as a separate versioned artifact.

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_select.py
Writes results/a4/selection.json and artifacts/a4/export/<model_version>/ . Does not read the holdout.
"""
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from ml.src.a4_common import choose_thresholds, load_a4, metrics, review_stats

ML = Path(__file__).resolve().parents[1]
RUNS, ART = ML / "results/a4/runs", ML / "artifacts/a4"


def val_metrics(run):
    return json.loads((RUNS / run / "metrics_val.json").read_text())


def seed_family(prefix):
    runs = sorted(p.name for p in RUNS.glob(f"{prefix}_s*") if (p / "metrics_val.json").exists())
    if not runs:
        return None
    vals = {r: val_metrics(r) for r in runs}
    e2e = np.array([vals[r]["e2e_macro_f1"] for r in runs])
    order = np.argsort(e2e)
    median_run = runs[order[len(runs) // 2]]
    return {"runs": runs, "e2e_per_seed": dict(zip(runs, e2e.round(4).tolist())), "e2e_mean": round(float(e2e.mean()), 4),
            "e2e_std": round(float(e2e.std(ddof=1)), 4) if len(runs) > 1 else None,
            "gate_mean": round(float(np.mean([vals[r]["gate_macro_f1"] for r in runs])), 4),
            "category_mean": round(float(np.mean([vals[r]["category_macro_f1"] for r in runs])), 4),
            "trans_recall_mean": round(float(np.mean([vals[r]["recall_TRANS"] for r in runs])), 4),
            "ux_recall_mean": round(float(np.mean([vals[r]["recall_UX"] for r in runs])), 4),
            "median_seed_run": median_run}


def main() -> int:
    lab = load_a4()
    va = lab[(lab.a4_split == "val") & (lab.label_final != "UNCLEAR")]
    y = va.label_final.values
    table, log = {}, []
    for r in ["E0_baseline_v1", "E1_tfidf_a4", "E2_tfidf_a4_synth", "E5_e5_lr"]:
        if (RUNS / r / "metrics_val.json").exists():
            m = val_metrics(r)
            table[r] = {"e2e": m["e2e_macro_f1"], "gate": m["gate_macro_f1"], "category": m["category_macro_f1"],
                        "trans_recall": m["recall_TRANS"], "ux_recall": m["recall_UX"]}
    fams = {k: seed_family(k) for k in ["E3_marbert_final", "E4_marbert_synth"]}
    for k, f in fams.items():
        if f:
            table[k] = {"e2e": f["e2e_mean"], "e2e_std": f["e2e_std"], "gate": f["gate_mean"], "category": f["category_mean"],
                        "trans_recall": f["trans_recall_mean"], "ux_recall": f["ux_recall_mean"], "median_seed_run": f["median_seed_run"]}

    # rule 3: synthetic retained only with >= 0.005 val e2e gain for the same architecture
    classical = "E1_tfidf_a4"
    if "E2_tfidf_a4_synth" in table and table["E2_tfidf_a4_synth"]["e2e"] >= table["E1_tfidf_a4"]["e2e"] + 0.005:
        classical = "E2_tfidf_a4_synth"
    log.append(f"classical candidate: {classical}")
    transformer = "E3_marbert_final" if "E3_marbert_final" in table else None
    if transformer and "E4_marbert_synth" in table and table["E4_marbert_synth"]["e2e"] >= table[transformer]["e2e"] + 0.005:
        transformer = "E4_marbert_synth"
    log.append(f"transformer candidate: {transformer}")
    # cheap candidates: classical vs e5 (ties < 0.005 -> cheaper = classical)
    current = classical
    if "E5_e5_lr" in table and table["E5_e5_lr"]["e2e"] >= table[classical]["e2e"] + 0.005:
        current = "E5_e5_lr"
    log.append(f"best non-fine-tuned candidate: {current}")
    if transformer:
        gain = table[transformer]["e2e"] - table[current]["e2e"]
        gate_drop = table[current]["gate"] - table[transformer]["gate"]
        ok = gain >= 0.02 and gate_drop <= 0.01
        log.append(f"transformer gain {gain:+.4f} (need >= 0.02), gate drop {gate_drop:+.4f} (need <= 0.01) -> {'REPLACE' if ok else 'keep'}")
        if ok:
            current = transformer
    selected = current
    log.append(f"SELECTED: {selected}")

    # thresholds on validation for every candidate (transformers: re-scored from the exported fp16 artifact)
    def val_probs(name):
        if name in fams and fams[name]:
            from ml.src.hf_model import HFPredictor
            run = fams[name]["median_seed_run"]
            return HFPredictor(ART / run).predict_proba(va.review.tolist()), run
        return np.load(RUNS / name / "val_probs.npy"), name

    cands = {}
    for name in [n for n in ["E0_baseline_v1", "E1_tfidf_a4", "E2_tfidf_a4_synth", "E5_e5_lr", "E3_marbert_final", "E4_marbert_synth"] if n in table]:
        P, run = val_probs(name)
        th = choose_thresholds(P, y)
        cands[name] = {"artifact_run": run, "thresholds": th, "val_metrics_from_artifact": metrics(P, y)["e2e_macro_f1"],
                       "val_review": review_stats(P, y, th)}
    sel_run = cands[selected]["artifact_run"]
    th = cands[selected]["thresholds"]

    # export selected model as a separate, versioned artifact (does not touch ml/artifacts used by Codex)
    if selected.startswith("E3") or selected.startswith("E4"):
        version, backend = "a4-marbert-v1", "hf-7way"
    elif selected.startswith("E5"):
        version, backend = "a4-e5lr-v1", "e5-lr"
    else:
        version, backend = "a4-tfidf-v1", "sklearn-two-stage"
    exp = ART / "export" / version
    if exp.exists():
        shutil.rmtree(exp)
    exp.mkdir(parents=True)
    if backend == "hf-7way":
        shutil.copytree(ART / sel_run, exp / "model")
        files = {"model_dir": "model"}
    elif backend == "sklearn-two-stage":
        src = ART / sel_run if (ART / sel_run).exists() else ML / "artifacts/baseline-v1"
        shutil.copy(src / "gate.joblib", exp / "gate.joblib")
        shutil.copy(src / "category.joblib", exp / "category.joblib")
        files = {"gate": "gate.joblib", "category": "category.joblib"}
    else:
        print("e5-lr export is not supported by infer.py; would need a backend first.")
        return 1
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ML, capture_output=True, text=True).stdout.strip()
    manifest = {"model_version": version, "backend": backend, "files": files,
                "categories": ["AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER"],
                "thresholds": {"gate_decision": 0.5, **th, "precision_target": 0.9},
                "selected_candidate": selected, "artifact_run": sel_run,
                "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "code_commit": commit,
                "label_provenance": "AI-assisted reference labels (A4: sonnet+fable coders, opus adjudicator; v1: sonnet+haiku+sonnet). NOT human gold.",
                "score_semantics": {"complaint_score": "1 - P(NO) (hf-7way, temperature-scaled) or gate P(complaint) (sklearn)",
                                    "category_score": "P(category | complaint)", "needs_review": "gate score in [gate_review_low, gate_review_high) or category_score < category_review"}}
    (exp / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    sel = {"rule": "configs/a4_selection_rule.yaml", "decided_utc": manifest["created_utc"], "code_commit": commit,
           "validation_table": table, "families": fams, "decision_log": log, "selected": selected, "model_version": version,
           "export_dir": str(exp.relative_to(ML)), "candidates": cands, "holdout_used": False}
    (ML / "results/a4/selection.json").write_text(json.dumps(sel, indent=2, ensure_ascii=False))
    print(json.dumps({"table": table, "log": log, "thresholds": th}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
