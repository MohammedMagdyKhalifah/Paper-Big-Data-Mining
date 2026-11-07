"""Build the cleaned corpus, duplicate groups and the annotation sample.

Usage (from repo root):  PYTHONPATH=. ml/.venv/bin/python ml/scripts/prepare_data.py
Outputs:
  ml/data/interim/corpus.parquet             all records + exclusion + dup_group (local only)
  ml/data/annotation/sample.parquet          the frozen annotation sample with metadata
  ml/data/annotation/batches/*.jsonl         id + text only (what coders see)
  ml/reports/record_flow.json                counts per stage
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ml.src.dedup import group_duplicates, text_hash
from ml.src.text import exclusion_reason, p0, p1

ML = Path(__file__).resolve().parents[1]
RAW, INTERIM, ANN = ML / "data" / "raw", ML / "data" / "interim", ML / "data" / "annotation"
SEED = 42
PILOT_N = 100
TARGET = {"cls_external": 300, "gov": 1000, "nongov": 700}
NEG_SHARE = 0.75          # negative-weighted, not negative-only
PER_APP_CAP_GOV = 90      # avoid one app (e.g. Absher) dominating
PER_APP_CAP_NONGOV = 60
BATCH_SIZE = 238


def load_domains():
    cfg = yaml.safe_load((ML / "configs" / "app_domains.yaml").read_text(encoding="utf-8"))
    lookup = {}
    for domain in ("gov", "utility", "finance", "telecom", "commerce_delivery"):
        for canon, aliases in cfg[domain].items():
            for a in aliases:
                lookup[a] = (domain, canon)
    for a in cfg["games"]:
        lookup[a] = ("games", a)
    return lookup, cfg["default_domain"]


def build_corpus() -> pd.DataFrame:
    s = pd.read_parquet(RAW / "aura_sentiment.parquet")
    c = pd.read_csv(RAW / "aura_classification_v2.csv")
    s = s.assign(source="aura_sentiment", record_id=[f"S{i:05d}" for i in range(len(s))], aura_label=None)
    c = c.assign(source="aura_classification_v2", record_id=[f"C{i:04d}" for i in range(len(c))], sentiment=None)
    c = c.rename(columns={"label": "aura_label"})
    df = pd.concat([s, c], ignore_index=True)[
        ["record_id", "source", "appName", "platform", "sentiment", "aura_label", "review"]]
    lookup, default = load_domains()
    dom = df.appName.map(lambda a: lookup.get(a, (default, a)))
    df["domain"] = [d for d, _ in dom]
    df["app_canonical"] = [k for _, k in dom]
    df["exclusion_reason"] = df.review.map(exclusion_reason)
    df["text_p0"] = df.review.map(p0)
    df["text_p1"] = df.review.map(p1)
    df["text_hash"] = df.text_p1.map(text_hash)
    return df


def stratified_take(pool: pd.DataFrame, n: int, cap: int, rng) -> pd.DataFrame:
    """Round-robin over apps (shuffled) so that every app contributes, capped per app."""
    pool = pool.sample(frac=1.0, random_state=rng.integers(1 << 31))
    by_app = {a: g.index.tolist() for a, g in pool.groupby("app_canonical")}
    taken, counts = [], {a: 0 for a in by_app}
    apps = list(by_app)
    while len(taken) < n and apps:
        nxt = []
        for a in apps:
            if len(taken) >= n:
                break
            if by_app[a] and counts[a] < cap:
                taken.append(by_app[a].pop())
                counts[a] += 1
                nxt.append(a)
        apps = nxt
    return pool.loc[taken]


def main() -> int:
    rng = np.random.default_rng(SEED)
    INTERIM.mkdir(parents=True, exist_ok=True)
    (ANN / "batches").mkdir(parents=True, exist_ok=True)
    df = build_corpus()
    flow = {"raw_total": int(len(df)), "raw_by_source": df.source.value_counts().to_dict()}
    flow["excluded_by_reason"] = df.exclusion_reason.value_counts().to_dict()

    # Duplicate groups are computed over ALL records (both datasets) so cross-source copies share a group.
    groups, pairs = group_duplicates(df.text_p1.tolist(), threshold=0.85)
    df["dup_group"] = [f"G{g:05d}" for g in groups]
    df.to_parquet(INTERIM / "corpus.parquet", index=False)
    (INTERIM / "near_duplicate_pairs.json").write_text(json.dumps(
        [{"a": df.record_id[a], "b": df.record_id[b], "cos": round(s, 3)} for a, b, s in pairs], ensure_ascii=False))
    gsize = df.dup_group.value_counts()
    flow["dup_groups"] = int(gsize.size)
    flow["records_in_multi_member_groups"] = int(gsize[gsize > 1].sum())
    flow["largest_group_size"] = int(gsize.max())
    flow["near_duplicate_pairs"] = len(pairs)

    # One representative per duplicate group; prefer the AURA-Classification member (has a human label).
    elig = df[df.exclusion_reason.isna() & (df.domain != "games")].copy()
    flow["eligible_non_game"] = int(len(elig))
    elig["_pref"] = (elig.source != "aura_classification_v2").astype(int)
    group_label = (df.dropna(subset=["aura_label"]).groupby("dup_group").aura_label
                   .agg(lambda x: x.mode().iat[0]))
    reps = elig.sort_values(["_pref", "record_id"]).drop_duplicates("dup_group").drop(columns="_pref")
    reps["group_aura_label"] = reps.dup_group.map(group_label)
    flow["eligible_unique_groups"] = int(len(reps))

    # (1) external-check slice: groups carrying an AURA human label, stratified by that label.
    cls_pool = reps[reps.group_aura_label.notna()]
    per_label = TARGET["cls_external"] // cls_pool.group_aura_label.nunique()
    # (explicit loop: pandas>=3 groupby.apply drops the grouping column)
    cls_take = pd.concat([g.sample(min(len(g), per_label), random_state=SEED)
                          for _, g in cls_pool.groupby("group_aura_label")])
    rest = reps.drop(cls_take.index)
    rest = rest[rest.source == "aura_sentiment"]

    parts = [cls_take.assign(stratum="cls_external")]
    for stratum, mask, cap in [("gov", rest.domain == "gov", PER_APP_CAP_GOV),
                               ("nongov", rest.domain != "gov", PER_APP_CAP_NONGOV)]:
        pool = rest[mask]
        n = TARGET[stratum]
        n_neg = int(round(n * NEG_SHARE))
        neg = stratified_take(pool[pool.sentiment == "negative"], n_neg, cap, rng)
        pos = stratified_take(pool[pool.sentiment == "positive"], n - len(neg), cap, rng)
        parts.append(pd.concat([neg, pos]).assign(stratum=stratum))
    sample = pd.concat(parts).sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    assert sample.dup_group.is_unique

    sample["ann_id"] = [f"A{i:04d}" for i in range(len(sample))]
    sample["phase"] = ["pilot" if i < PILOT_N else "main" for i in range(len(sample))]
    sample.to_parquet(ANN / "sample.parquet", index=False)
    flow["annotation_sample"] = {k: int(v) for k, v in sample.stratum.value_counts().items()}
    flow["annotation_sample_by_domain"] = {k: int(v) for k, v in sample.domain.value_counts().items()}
    flow["annotation_sample_sentiment"] = {k: int(v) for k, v in sample.sentiment.value_counts(dropna=False).items()}

    # Coders see only an opaque id and the privacy-masked P0 text.
    def dump(frame, path):
        with open(path, "w", encoding="utf-8") as f:
            for r in frame.itertuples():
                f.write(json.dumps({"id": r.ann_id, "text": r.text_p0}, ensure_ascii=False) + "\n")

    dump(sample[sample.phase == "pilot"], ANN / "batches" / "pilot.jsonl")
    main_part = sample[sample.phase == "main"].reset_index(drop=True)
    for b, start in enumerate(range(0, len(main_part), BATCH_SIZE)):
        dump(main_part.iloc[start:start + BATCH_SIZE], ANN / "batches" / f"main_{b:02d}.jsonl")

    (ML / "reports").mkdir(exist_ok=True)
    (ML / "reports" / "record_flow.json").write_text(json.dumps(flow, indent=2, ensure_ascii=False))
    print(json.dumps(flow, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
