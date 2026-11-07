"""A4 Phase 2: confident-learning scan of the v1 TRAIN+VAL labels (the v1 test split is never touched).

Out-of-fold probabilities (5-fold StratifiedGroupKFold, char TF-IDF + calibrated LR = the v1 category architecture,
on the 7-way joint label NO/AUTH/AVAIL/PERF/TRANS/UX/OTHER; UNCLEAR excluded) feed cleanlab.find_label_issues.
Flagged items are NOT relabelled here; they go to independent AI re-adjudication (scripts/a4_build_labels.py).

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_label_issues.py
Outputs: data/a4/label_issues_v1.csv, results/a4/label_issues_summary.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from cleanlab.filter import find_label_issues
from sklearn.model_selection import StratifiedGroupKFold

from ml.src.models import build

ML = Path(__file__).resolve().parents[1]
SEED = 42
LABELS7 = ["NO", "AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER"]


def main() -> int:
    lab = pd.read_parquet(ML / "data/annotation/labels.parquet")
    split = pd.read_csv(ML / "data/splits/split_manifest.csv")[["ann_id", "split"]]
    df = lab.merge(split, on="ann_id", validate="1:1")
    df = df[df.split.isin(["train", "val"]) & (df.label_final != "UNCLEAR")].reset_index(drop=True)
    y = df.label_final.map({l: i for i, l in enumerate(LABELS7)}).to_numpy()
    oof = np.zeros((len(df), len(LABELS7)))
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=SEED).split(df, y, df.dup_group):
        m = build("P1", "char25", 2, "lr_cal", C=1.0, class_weight="balanced", n_min_class=5)
        m.fit(df.review.iloc[tr].tolist(), y[tr])
        p = m.predict_proba(df.review.iloc[te].tolist())
        oof[np.ix_(te, m.classes_)] = p
    issues = find_label_issues(y, oof, return_indices_ranked_by="self_confidence", filter_by="prune_by_noise_rate")
    out = df.loc[issues, ["ann_id", "label_final", "label_a", "label_b", "adjudicated", "uncertain", "text_p0"]].copy()
    out["oof_pred"] = [LABELS7[i] for i in oof[issues].argmax(1)]
    out["oof_given_prob"] = oof[issues, y[issues]].round(3)
    out["oof_pred_prob"] = oof[issues].max(1).round(3)
    (ML / "data/a4").mkdir(parents=True, exist_ok=True)
    (ML / "results/a4").mkdir(parents=True, exist_ok=True)
    out.to_csv(ML / "data/a4/label_issues_v1.csv", index=False)
    summ = {"n_scanned": int(len(df)), "n_flagged": int(len(out)),
            "flagged_by_given_label": out.label_final.value_counts().to_dict(),
            "flagged_given_to_pred": {f"{a}->{b}": int(n) for (a, b), n in
                                      out.groupby(["label_final", "oof_pred"]).size().sort_values(ascending=False).head(15).items()},
            "flag_rate_adjudicated": float(out.adjudicated.mean()),
            "base_rate_adjudicated": float(df.adjudicated.mean()),
            "oof_macro_f1_7way": float(__import__("sklearn.metrics", fromlist=["f1_score"]).f1_score(y, oof.argmax(1), average="macro"))}
    (ML / "results/a4/label_issues_summary.json").write_text(json.dumps(summ, indent=2, ensure_ascii=False))
    print(json.dumps(summ, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
