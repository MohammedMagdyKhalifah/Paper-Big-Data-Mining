"""A4: merge all AI-assisted annotations into one provenance-tracked table.

Sets:  v1_train / v1_val / v1_test (v1 labels; flagged v1 train/val items re-reviewed),
       holdout (frozen A4 evaluation set), a4_train (training expansion), synthetic (training-only augmentation).
Rules: two coders agree -> that label; disagree -> adjudicator. Re-review: blind relabel agrees -> v1 label kept
       (confirmed); disagrees -> adjudicator decides, with a reason. v1_test labels are never modified.

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/a4_build_labels.py [--allow-missing-train]
Outputs: data/a4/labels_a4.parquet, results/a4/agreement_a4.json, reports/a4_annotation_provenance.md
"""
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from ml.src.agreement import agreement, joint_label, load_coder

ML = Path(__file__).resolve().parents[1]
A4 = ML / "data" / "a4"
OUT = A4 / "out"
MODELS = {  # Claude Code subagent aliases; IDs per the session environment listing
    "sonnet": "Claude Sonnet 5.5 (claude-sonnet-5-5)", "fable": "Claude Fable 5.1 (claude-fable-5-1)",
    "opus": "Claude Opus 5.5 (claude-opus-5-5)", "haiku": "Claude Haiku 4.5 (claude-haiku-4-5-20251001)"}


def batch_ids(name):
    return [json.loads(l)["id"] for l in (A4 / "batches" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def merge_pair(prefix, problems):
    """Return DataFrame indexed by id with label_a, label_b, final fields for all batches with this prefix."""
    rows = []
    for bf in sorted((A4 / "batches").glob(f"{prefix}_*.jsonl")):
        b = bf.stem
        ids = batch_ids(b)
        a, pa = load_coder(OUT / f"coderA_{b}.jsonl", ids) if (OUT / f"coderA_{b}.jsonl").exists() else (None, ["missing file"])
        bb, pb = load_coder(OUT / f"coderB_{b}.jsonl", ids) if (OUT / f"coderB_{b}.jsonl").exists() else (None, ["missing file"])
        if pa or pb:
            problems += [f"{b}: A {pa[:2]} B {pb[:2]}"]
            continue
        ja = {i: joint_label(a.loc[i].is_complaint, a.loc[i].category) for i in ids}
        jb = {i: joint_label(bb.loc[i].is_complaint, bb.loc[i].category) for i in ids}
        dis = [i for i in ids if ja[i] != jb[i]]
        adj = pd.DataFrame()
        if dis:
            p = OUT / f"adjudication_{b}.jsonl"
            if not p.exists():
                problems.append(f"{b}: adjudication missing")
                continue
            adj, pr = load_coder(p, dis)
            if pr:
                problems.append(f"{b}: adjudication {pr[:2]}")
                continue
        for i in ids:
            src = adj.loc[i] if i in dis else a.loc[i]
            rows.append({"item_id": i, "batch": b, "label_a": ja[i], "label_b": jb[i], "adjudicated": i in dis,
                         "is_complaint": src.is_complaint, "category": src.category,
                         "label_final": joint_label(src.is_complaint, src.category),
                         "multi_issue": bool(src.multi_issue), "negation": bool(src.negation),
                         "uncertain": bool(a.loc[i].uncertain or bb.loc[i].uncertain or (i in dis and adj.loc[i].uncertain))})
    return pd.DataFrame(rows).set_index("item_id") if rows else pd.DataFrame()


def main() -> int:
    allow_missing_train = "--allow-missing-train" in sys.argv
    problems = []
    # ---------------- v1 items (+ re-review) ----------------
    v1 = pd.read_parquet(ML / "data/annotation/labels.parquet")
    sp = pd.read_csv(ML / "data/splits/split_manifest.csv")[["ann_id", "split"]]
    v1 = v1.merge(sp, on="ann_id", validate="1:1").set_index("ann_id")
    rr_ids = batch_ids("rereview_00")
    v1f, _ = load_coder(OUT / "v1final_rereview_00.jsonl", rr_ids)
    fb, p1 = load_coder(OUT / "fableblind_rereview_00.jsonl", rr_ids)
    rr_dis = [i for i in rr_ids if joint_label(v1f.loc[i].is_complaint, v1f.loc[i].category) != joint_label(fb.loc[i].is_complaint, fb.loc[i].category)]
    adj_rr, p2 = load_coder(OUT / "adjudication_rereview_00.jsonl", rr_dis)
    problems += [f"rereview: {x}" for x in p1 + p2]
    reasons = {}
    for l in (OUT / "adjudication_rereview_00.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            reasons[r["id"]] = r.get("reason", "")
    v1_rows = []
    for i, r in v1.iterrows():
        row = {"item_id": i, "record_id": r.record_id, "set": f"v1_{r.split}", "stratum": r.stratum, "dup_group": r.dup_group,
               "domain": r.domain, "app_canonical": r.app_canonical, "review": r.review, "text_p0": r.text_p0,
               "label_v1": r.label_final, "label_a": r.label_a, "label_b": r.label_b, "adjudicated": bool(r.adjudicated),
               "coder_a_model": MODELS["sonnet"], "coder_b_model": MODELS["haiku"], "adjudicator_model": MODELS["sonnet"],
               "guide_version": "v1.0", "is_complaint": r.is_complaint, "category": r.category, "label_final": r.label_final,
               "multi_issue": bool(r.multi_issue), "negation": bool(r.negation), "uncertain": bool(r.uncertain),
               "rereview_flagged": False, "rereview_blind_label": None, "modified_in_a4": False, "modification_reason": None}
        if i in rr_ids and r.split in ("train", "val"):
            row["rereview_flagged"] = True
            row["rereview_blind_label"] = joint_label(fb.loc[i].is_complaint, fb.loc[i].category)
            if i in rr_dis:
                n = adj_rr.loc[i]
                new = joint_label(n.is_complaint, n.category)
                row.update({"is_complaint": n.is_complaint, "category": n.category, "label_final": new,
                            "uncertain": bool(n.uncertain) or row["uncertain"], "guide_version": "v1.1 (re-adjudicated)",
                            "modified_in_a4": new != r.label_final,
                            "modification_reason": f"re-review: blind {MODELS['fable']} disagreed; {MODELS['opus']} adjudicated: {reasons.get(i, '')}"})
        v1_rows.append(row)
    v1t = pd.DataFrame(v1_rows).set_index("item_id")

    # ---------------- A4 holdout + training expansion ----------------
    frames = [v1t]
    stats = {}
    for prefix, sample_file, set_name in [("holdout", "holdout_sample.parquet", "holdout"), ("train", "train_expansion_sample.parquet", "a4_train")]:
        sub_problems = []
        lab = merge_pair(prefix, sub_problems)
        if not (set_name == "a4_train" and allow_missing_train):
            problems += sub_problems
        smp = pd.read_parquet(A4 / sample_file).set_index("ann_id")
        if lab.empty or len(lab) < len(smp):
            if set_name == "a4_train" and allow_missing_train:
                print(f"NOTE: a4_train incomplete ({len(lab)}/{len(smp)}) - skipped (--allow-missing-train)")
                continue
        lab = smp[["record_id", "stratum", "dup_group", "domain", "app_canonical", "review", "text_p0"]].join(lab, how="inner")
        lab = lab.assign(set=set_name, label_v1=None, coder_a_model=MODELS["sonnet"], coder_b_model=MODELS["fable"],
                         adjudicator_model=MODELS["opus"], guide_version="v1.1", rereview_flagged=False,
                         rereview_blind_label=None, modified_in_a4=False, modification_reason=None)
        frames.append(lab.drop(columns="batch"))
        A = lab.label_a.map(lambda x: x if x in ("NO", "UNCLEAR") else "YES")
        B = lab.label_b.map(lambda x: x if x in ("NO", "UNCLEAR") else "YES")
        both = ~lab.label_a.isin(["NO", "UNCLEAR"]) & ~lab.label_b.isin(["NO", "UNCLEAR"])
        stats[set_name] = {"n": int(len(lab)), "complaint_kappa": float(cohen_kappa_score(A, B)),
                           "joint_kappa": float(cohen_kappa_score(lab.label_a, lab.label_b)),
                           "joint_pct_agree": float((lab.label_a == lab.label_b).mean()),
                           "category_kappa_both_yes": float(cohen_kappa_score(lab.label_a[both], lab.label_b[both])),
                           "n_adjudicated": int(lab.adjudicated.sum()), "uncertain_rate": float(lab.uncertain.mean()),
                           "final_distribution": lab.label_final.value_counts().to_dict(),
                           "by_stratum": {s: g.label_final.value_counts().to_dict() for s, g in lab.groupby("stratum")}}

    # ---------------- synthetic (training only, verified) ----------------
    syn_b = A4 / "batches/synthetic_00.jsonl"
    if syn_b.exists() and (OUT / "fableverify_synthetic_00.jsonl").exists():
        ids = batch_ids("synthetic_00")
        ver, pv = load_coder(OUT / "fableverify_synthetic_00.jsonl", ids)
        problems += [f"synthetic verify: {x}" for x in pv]
        intended = pd.read_json(A4 / "synthetic/intended_labels.jsonl", lines=True).set_index("id")
        texts = {json.loads(l)["id"]: json.loads(l)["text"] for l in syn_b.read_text(encoding="utf-8").splitlines() if l.strip()}
        srows = []
        for i in ids:
            it = intended.loc[i]
            want = joint_label(it.is_complaint, it.category if it.is_complaint == "yes" else None)
            got = joint_label(ver.loc[i].is_complaint, ver.loc[i].category)
            srows.append({"item_id": i, "record_id": None, "set": "synthetic", "stratum": f"syn_{it.kind}", "dup_group": f"SYN-{i}",
                          "domain": "synthetic", "app_canonical": "synthetic", "review": texts[i], "text_p0": texts[i],
                          "label_v1": None, "label_a": want, "label_b": got, "adjudicated": False,
                          "coder_a_model": f"generator intent: {MODELS['sonnet']}", "coder_b_model": f"blind verifier: {MODELS['fable']}",
                          "adjudicator_model": None, "guide_version": "v1.1", "is_complaint": it.is_complaint,
                          "category": it.category if it.is_complaint == "yes" else None, "label_final": want,
                          "multi_issue": False, "negation": False, "uncertain": False, "rereview_flagged": False,
                          "rereview_blind_label": None, "modified_in_a4": False,
                          "modification_reason": None if want == got else "REJECTED: blind verifier disagreed with intended label",
                          "synthetic_verified": want == got})
        syn = pd.DataFrame(srows).set_index("item_id")
        frames.append(syn)
        stats["synthetic"] = {"n_generated": int(len(syn)), "n_verified": int(syn.synthetic_verified.sum()),
                              "verified_by_kind": syn.groupby("stratum").synthetic_verified.mean().round(3).to_dict()}
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        return 1
    allt = pd.concat(frames)
    if "synthetic_verified" not in allt:
        allt["synthetic_verified"] = None
    allt.index.name = "item_id"
    assert allt.index.is_unique
    allt.reset_index().to_parquet(A4 / "labels_a4.parquet", index=False)

    rv = v1t[v1t.rereview_flagged]
    stats["v1_rereview"] = {"n_flagged_train_val": int(len(rv)), "blind_agreed": int(len(rv) - len(rr_dis)),
                            "adjudicated": len(rr_dis), "label_changed": int(rv.modified_in_a4.sum()),
                            "changes": {f"{a}->{b}": int(n) for (a, b), n in rv[rv.modified_in_a4].groupby(["label_v1", "label_final"]).size().items()}}
    stats["set_sizes"] = allt.set.value_counts().to_dict()
    (ML / "results/a4").mkdir(parents=True, exist_ok=True)
    (ML / "results/a4/agreement_a4.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
