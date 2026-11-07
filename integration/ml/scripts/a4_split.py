"""A4 split (pre-registered in configs/a4_selection_rule.yaml).

pool = v1_train + v1_val + a4_train  -> StratifiedGroupKFold(7, seed 42) on label_final grouped by dup_group:
        fold 0 = a4 'val', others = a4 'train'.
holdout -> 'holdout' (frozen), v1_test -> 'v1_test' (excluded from training), verified synthetic -> 'train_synthetic',
rejected synthetic -> 'excluded'.
Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_split.py
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

ML = Path(__file__).resolve().parents[1]


def main() -> int:
    lab = pd.read_parquet(ML / "data/a4/labels_a4.parquet")
    if not (lab.set == "a4_train").any():
        print("a4_train labels missing; build labels first.")
        return 1
    split = pd.Series(index=lab.index, dtype=object)
    split[lab.set == "holdout"] = "holdout"
    split[lab.set == "v1_test"] = "v1_test"
    syn = lab.set == "synthetic"
    split[syn & (lab.synthetic_verified == True)] = "train_synthetic"  # noqa: E712
    split[syn & (lab.synthetic_verified != True)] = "excluded"         # noqa: E712
    pool = lab[lab.set.isin(["v1_train", "v1_val", "a4_train"])]
    sgkf = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=42)
    _, val_idx = next(iter(sgkf.split(pool, pool.label_final, pool.dup_group)))
    split[pool.index] = "train"
    split[pool.index[val_idx]] = "val"
    lab["a4_split"] = split
    # leakage guards
    for a, b in [("train", "val"), ("train", "holdout"), ("val", "holdout"), ("train", "v1_test"), ("val", "v1_test"), ("holdout", "v1_test")]:
        assert not (set(lab.dup_group[lab.a4_split == a]) & set(lab.dup_group[lab.a4_split == b])), (a, b)
    out = lab[["item_id", "record_id", "set", "dup_group", "label_final", "a4_split"]]
    out.to_csv(ML / "data/a4/split_a4.csv", index=False)
    h = hashlib.sha256("\n".join(f"{i},{s}" for i, s in sorted(zip(out.item_id, out.a4_split))).encode()).hexdigest()
    info = {"sha256": h, "counts": out.a4_split.value_counts().to_dict(),
            "by_label": pd.crosstab(out.label_final, out.a4_split).to_dict()}
    (ML / "data/a4/split_a4_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
