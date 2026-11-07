"""A4: freeze a NEW evaluation holdout first, then draw the training expansion from the remaining pool.

Pool = eligible (non-excluded, non-game) AURA-Sentiment representatives, one per duplicate group, whose group
(a) contains no v1-annotated item and (b) contains no AURA-Classification record (kept for the external human check).

HOLDOUT (seed 2026, drawn before any A4 labeling or training):
  random   900 : gov 500 / non-gov 400, negative 75%, per-app caps      -> representative estimate
  enriched 340 : TRANS-lexicon 150, UX-lexicon 150, code-switch 40      -> estimates for weak classes
TRAINING EXPANSION (seed 2027, from what remains):
  random 1,800 | TRANS-lexicon 700 | UX-lexicon 300 | all remaining code-switch |
  model-guided: baseline-v1 predicts TRANS/UX 350, baseline gate uncertain (0.3-0.7) 350 | random top-up to 4,000.

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_prepare.py
Refuses to overwrite an existing frozen holdout.
"""
import json
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

ML = Path(__file__).resolve().parents[1]
A4 = ML / "data" / "a4"
BATCH = 250
PLACEHOLDERS = {"url", "email", "phone", "num", "user"}


def stratified_take(pool, n, cap, seed):
    """Round-robin over apps (shuffled) so every app contributes, capped per app (same rule as v1)."""
    pool = pool.sample(frac=1.0, random_state=seed)
    by_app = {a: g.index.tolist() for a, g in pool.groupby("app_canonical")}
    taken, counts, apps = [], {a: 0 for a in by_app}, list(by_app)
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


def representative(pool, n_gov, n_nongov, seed):
    parts = []
    for mask, n, cap in [(pool.domain == "gov", n_gov, 120), (pool.domain != "gov", n_nongov, 80)]:
        p = pool[mask]
        n_neg = int(round(n * 0.75))
        neg = stratified_take(p[p.sentiment == "negative"], n_neg, cap, seed)
        pos = stratified_take(p[p.sentiment == "positive"], n - len(neg), cap, seed + 1)
        parts.append(pd.concat([neg, pos]))
    return pd.concat(parts)


def latin_words(t):
    return len([w for w in re.findall(r"[A-Za-z]{2,}", t) if w.lower() not in PLACEHOLDERS])


def dump(frame, prefix):
    frame = frame.reset_index(drop=True)
    for b, start in enumerate(range(0, len(frame), BATCH)):
        with open(A4 / "batches" / f"{prefix}_{b:02d}.jsonl", "w", encoding="utf-8") as f:
            for r in frame.iloc[start:start + BATCH].itertuples():
                f.write(json.dumps({"id": r.ann_id, "text": r.text_p0}, ensure_ascii=False) + "\n")


def main() -> int:
    if (A4 / "holdout_sample.parquet").exists():
        print("Holdout already frozen; refusing to resample.")
        return 1
    (A4 / "batches").mkdir(parents=True, exist_ok=True)
    corpus = pd.read_parquet(ML / "data/interim/corpus.parquet")
    v1 = pd.read_parquet(ML / "data/annotation/sample.parquet")
    lx = yaml.safe_load((ML / "configs/a4_lexicons.yaml").read_text(encoding="utf-8"))
    cls_groups = set(corpus.dup_group[corpus.source == "aura_classification_v2"])
    el = corpus[corpus.exclusion_reason.isna() & (corpus.domain != "games")]
    pool = el[~el.dup_group.isin(set(v1.dup_group)) & ~el.dup_group.isin(cls_groups) & (el.source == "aura_sentiment")]
    pool = pool.sort_values("record_id").drop_duplicates("dup_group").set_index("record_id", drop=False)
    pool["lex_trans"] = pool.text_p1.map(lambda t: any(w in t for w in lx["trans"]))
    pool["lex_ux"] = pool.text_p1.map(lambda t: any(w in t for w in lx["ux"]))
    pool["code_switch"] = pool.text_p0.map(latin_words) >= 1
    flow = {"pool": int(len(pool)), "pool_lex_trans": int(pool.lex_trans.sum()), "pool_lex_ux": int(pool.lex_ux.sum()),
            "pool_code_switch": int(pool.code_switch.sum())}

    # ---------------- HOLDOUT (frozen first) ----------------
    rnd = representative(pool, 500, 400, 2026).assign(stratum="random")
    rest = pool.drop(rnd.index)
    enr = []
    for col, n, name in [("lex_trans", 150, "enr_trans"), ("lex_ux", 150, "enr_ux"), ("code_switch", 40, "enr_codeswitch")]:
        cand = rest[rest[col]]
        take = cand.sample(min(n, len(cand)), random_state=2026)
        enr.append(take.assign(stratum=name))
        rest = rest.drop(take.index)
    hold = pd.concat([rnd] + enr).sample(frac=1.0, random_state=2026)
    hold["ann_id"] = [f"H{i:04d}" for i in range(len(hold))]
    assert hold.dup_group.is_unique

    # ---------------- TRAINING EXPANSION ----------------
    gate = joblib.load(ML / "artifacts/baseline-v1/gate.joblib")
    cat = joblib.load(ML / "artifacts/baseline-v1/category.joblib")
    texts = rest.review.tolist()
    pg = gate.predict_proba(texts)[:, list(gate.classes_).index(1)]
    pc = cat.classes_[cat.predict_proba(texts).argmax(1)]
    rest = rest.assign(base_gate=pg, base_cat=pc)
    parts = [representative(rest, 1000, 800, 2027).assign(stratum="random")]
    rest2 = rest.drop(parts[0].index)
    plan = [("lex_trans", 700, "enr_trans"), ("lex_ux", 300, "enr_ux"), ("code_switch", 10 ** 6, "enr_codeswitch")]
    for col, n, name in plan:
        cand = rest2[rest2[col]]
        take = cand.sample(min(n, len(cand)), random_state=2027)
        parts.append(take.assign(stratum=name))
        rest2 = rest2.drop(take.index)
    guided = rest2[(rest2.base_gate >= 0.5) & rest2.base_cat.isin(["TRANS", "UX"])]
    take = guided.sample(min(350, len(guided)), random_state=2027)
    parts.append(take.assign(stratum="model_pred_trans_ux"))
    rest2 = rest2.drop(take.index)
    unc = rest2[(rest2.base_gate >= 0.3) & (rest2.base_gate < 0.7)]
    take = unc.sample(min(350, len(unc)), random_state=2027)
    parts.append(take.assign(stratum="model_uncertain_gate"))
    rest2 = rest2.drop(take.index)
    n_now = sum(len(p) for p in parts)
    if n_now < 4000:
        parts.append(rest2.sample(4000 - n_now, random_state=2028).assign(stratum="random_topup"))
    tr = pd.concat(parts).sample(frac=1.0, random_state=2027)
    tr["ann_id"] = [f"T{i:04d}" for i in range(len(tr))]
    assert tr.dup_group.is_unique and not (set(tr.dup_group) & set(hold.dup_group))

    keep = ["ann_id", "record_id", "source", "dup_group", "domain", "app_canonical", "sentiment", "stratum",
            "lex_trans", "lex_ux", "code_switch", "review", "text_p0", "text_p1"]
    hold[keep].to_parquet(A4 / "holdout_sample.parquet", index=False)
    tr[keep + ["base_gate", "base_cat"]].to_parquet(A4 / "train_expansion_sample.parquet", index=False)
    dump(hold, "holdout")
    dump(tr, "train")
    flow["holdout"] = hold.stratum.value_counts().to_dict()
    flow["holdout_domain"] = hold.domain.value_counts().to_dict()
    flow["train_expansion"] = tr.stratum.value_counts().to_dict()
    flow["train_expansion_domain"] = tr.domain.value_counts().to_dict()
    import hashlib
    flow["holdout_ids_sha256"] = hashlib.sha256("\n".join(sorted(hold.record_id)).encode()).hexdigest()
    (ML / "results/a4").mkdir(parents=True, exist_ok=True)
    (ML / "results/a4/sampling_flow.json").write_text(json.dumps(flow, indent=2, ensure_ascii=False))
    print(json.dumps(flow, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
