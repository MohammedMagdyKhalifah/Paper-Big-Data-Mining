"""Group-aware stratified 70/15/15 split of the labelled sample (seed fixed)."""
from __future__ import annotations

import hashlib

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

SEED = 42


def make_split(labels: pd.DataFrame, seed: int = SEED) -> pd.Series:
    """Return split ∈ {train, val, test} per row, stratified on label_final, grouped by dup_group.

    Uses StratifiedGroupKFold with 20 folds: 3 folds -> test (15%), 3 -> val (15%), 14 -> train (70%).
    """
    y = labels.label_final.values
    groups = labels.dup_group.values
    sgkf = StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=seed)
    fold = pd.Series(-1, index=labels.index)
    for k, (_, idx) in enumerate(sgkf.split(labels, y, groups)):
        fold.iloc[idx] = k
    split = pd.Series("train", index=labels.index)
    split[fold.isin([0, 1, 2])] = "test"
    split[fold.isin([3, 4, 5])] = "val"
    return split


def manifest_hash(df: pd.DataFrame) -> str:
    payload = "\n".join(f"{a},{g},{s}" for a, g, s in df[["ann_id", "dup_group", "split"]].sort_values("ann_id").values)
    return hashlib.sha256(payload.encode()).hexdigest()
