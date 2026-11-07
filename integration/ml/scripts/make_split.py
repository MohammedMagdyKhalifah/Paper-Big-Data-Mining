"""Freeze the train/val/test split.  Usage: PYTHONPATH=. ml/.venv/bin/python ml/scripts/make_split.py"""
import json
import sys
from pathlib import Path

import pandas as pd

from ml.src.split import SEED, make_split, manifest_hash

ML = Path(__file__).resolve().parents[1]


def main() -> int:
    out = ML / "data" / "splits" / "split_manifest.csv"
    lab = pd.read_parquet(ML / "data" / "annotation" / "labels.parquet")
    lab["split"] = make_split(lab).values
    if out.exists() and "--force" not in sys.argv:
        old = pd.read_csv(out)
        if manifest_hash(old) != manifest_hash(lab):
            print("Existing split differs from a fresh one; refusing to overwrite (use --force deliberately).")
            return 1
        print("Split already frozen and reproducible:", manifest_hash(old))
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    lab[["ann_id", "record_id", "dup_group", "label_final", "split"]].to_csv(out, index=False)
    h = manifest_hash(lab)
    counts = pd.crosstab(lab.label_final, lab.split)
    info = {"seed": SEED, "sha256": h, "n": int(len(lab)),
            "counts": {s: lab.split.value_counts()[s].item() for s in ("train", "val", "test")},
            "by_label": counts.to_dict()}
    (ML / "data" / "splits" / "split_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
