"""Merge coder A / coder B / adjudicator outputs into the reference label table + agreement report.

Usage (from repo root):  PYTHONPATH=. ml/.venv/bin/python ml/scripts/build_labels.py
Inputs : ml/data/annotation/out/coder{A,B}_{batch}.jsonl, ml/data/annotation/out/adjudication_{batch}.jsonl
Outputs: ml/data/annotation/labels.parquet, ml/reports/agreement.md, ml/results/agreement.json
Fails loudly if any item lacks a valid label from A, B, or (for disagreements) the adjudicator.
"""
import json
import sys
from pathlib import Path

import pandas as pd

from ml.src.agreement import CATS, agreement, crosstab, joint_label, load_coder

ML = Path(__file__).resolve().parents[1]
ANN = ML / "data" / "annotation"
OUT = ANN / "out"


def batches():
    return sorted(p.stem for p in (ANN / "batches").glob("*.jsonl"))


def ids_of(batch):
    return [json.loads(l)["id"] for l in (ANN / "batches" / f"{batch}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    sample = pd.read_parquet(ANN / "sample.parquet").set_index("ann_id")
    A, B, ADJ, problems = [], [], [], []
    for b in batches():
        ids = ids_of(b)
        for coder, acc in (("A", A), ("B", B)):
            df, p = load_coder(OUT / f"coder{coder}_{b}.jsonl", ids)
            problems += [f"coder{coder}/{b}: {x}" for x in p]
            acc.append(df.assign(batch=b))
        adj_path = OUT / f"adjudication_{b}.jsonl"
        if adj_path.exists():
            ADJ.append(adj_path)
    a, bb = pd.concat(A), pd.concat(B)
    ja = pd.Series([joint_label(x, y) for x, y in zip(a.is_complaint, a.category)], index=a.index)
    jb = pd.Series([joint_label(x, y) for x, y in zip(bb.is_complaint, bb.category)], index=bb.index)
    common = ja.index.intersection(jb.index)
    disagree = common[ja[common] != jb[common]]

    adj = pd.DataFrame()
    if ADJ:
        frames = []
        for p in ADJ:
            df, pr = load_coder(p, list(disagree))
            problems += [f"adjudication/{p.stem}: {x}" for x in pr if not x.startswith("missing")]
            frames.append(df)
        adj = pd.concat(frames)
        adj = adj[~adj.index.duplicated()]
    missing_adj = sorted(set(disagree) - set(adj.index))
    if missing_adj:
        problems.append(f"{len(missing_adj)} disagreements without adjudication: {missing_adj[:10]}")
    if problems:
        print("PROBLEMS:\n  " + "\n  ".join(problems))
        return 1

    rows = []
    for i in sample.index:
        ra, rb = a.loc[i], bb.loc[i]
        src = adj.loc[i] if i in disagree else ra
        rows.append({
            "ann_id": i,
            "label_a": joint_label(ra.is_complaint, ra.category),
            "label_b": joint_label(rb.is_complaint, rb.category),
            "is_complaint": src.is_complaint,
            "category": src.category,
            "label_final": joint_label(src.is_complaint, src.category),
            "adjudicated": i in disagree,
            "multi_issue": bool(src.multi_issue),
            "negation": bool(src.negation),
            "uncertain": bool(ra.uncertain or rb.uncertain or (i in disagree and adj.loc[i].uncertain)),
        })
    lab = pd.DataFrame(rows).set_index("ann_id")
    lab = sample[["record_id", "source", "dup_group", "domain", "app_canonical", "sentiment", "group_aura_label",
                  "stratum", "phase", "review", "text_p0"]].join(lab)
    lab.reset_index().to_parquet(ANN / "labels.parquet", index=False)

    # ---------------- agreement report ----------------
    stats = {"overall": agreement(a, bb)}
    for ph in ("pilot", "main"):
        ids = sample.index[sample.phase == ph]
        stats[ph] = agreement(a.loc[a.index.intersection(ids)], bb.loc[bb.index.intersection(ids)])
    stats["n_adjudicated"] = int(len(disagree))
    # External check: AI final is_complaint vs AURA human label (bug_report => technical complaint proxy).
    ext = lab[lab.group_aura_label.notna() & (lab.is_complaint != "unclear")]
    proxy = (ext.group_aura_label == "bug_report")
    ai = (ext.is_complaint == "yes")
    from sklearn.metrics import cohen_kappa_score
    stats["aura_proxy"] = {
        "n": int(len(ext)),
        "pct_agree": float((proxy == ai).mean()),
        "kappa": float(cohen_kappa_score(proxy, ai)),
        "crosstab": pd.crosstab(ext.group_aura_label, ext.is_complaint).to_dict(),
    }
    stats["final_distribution"] = lab.label_final.value_counts().to_dict()
    (ML / "results").mkdir(exist_ok=True)
    (ML / "results" / "agreement.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))

    labels8 = CATS + ["NO", "UNCLEAR"]
    ct = crosstab(ja[common], jb[common], labels8)
    o = stats["overall"]
    md = [
        "# Annotation Agreement Report",
        "",
        "**Provenance:** labels were produced by two independent **AI coders** (coder A = Claude Sonnet, coder B = Claude Haiku),",
        "each seeing only an opaque id and the privacy-masked text, following `annotation_guide.md`. Disagreements were resolved",
        "by an AI adjudicator (Claude Sonnet) shown both labels and the guide. Per the project owner's decision these serve as the",
        "reference labels; they are **not** independent human gold, and κ below is **inter-AI-annotator** agreement.",
        "",
        f"Generated by `scripts/build_labels.py`. Items: {len(lab)} (pilot {int((lab.phase=='pilot').sum())}, main {int((lab.phase=='main').sum())}).",
        "",
        "## Agreement (coder A vs coder B)",
        "| scope | n | complaint % agree | complaint κ | joint (8-way) % agree | joint κ | category κ (both yes) |",
        "|---|---|---|---|---|---|---|",
    ]
    for k in ("pilot", "main", "overall"):
        s = stats[k]
        md.append(f"| {k} | {s['n']} | {s['complaint_pct_agree']:.3f} | {s['complaint_kappa']:.3f} | "
                  f"{s['joint_pct_agree']:.3f} | {s['joint_kappa']:.3f} | {s.get('category_kappa', float('nan')):.3f} (n={s['category_n_both_yes']}) |")
    ap = stats["aura_proxy"]
    md += [
        "",
        f"Disagreements adjudicated: **{stats['n_adjudicated']}** ({stats['n_adjudicated']/o['n']:.1%}).",
        "",
        "## External check vs AURA human labels",
        f"On {ap['n']} items whose duplicate group carries an AURA-Classification v2 human label (unclear excluded):",
        f"AI `is_complaint=yes` vs AURA `bug_report`: agreement {ap['pct_agree']:.3f}, κ {ap['kappa']:.3f}.",
        "The constructs differ (AURA `bug_report` vs our *technical complaint*), so this is a proxy, not a gold comparison.",
        "",
        "| AURA label \\ AI is_complaint | " + " | ".join(sorted(ext.is_complaint.unique())) + " |",
        "|---|" + "---|" * ext.is_complaint.nunique(),
    ]
    xt = pd.crosstab(ext.group_aura_label, ext.is_complaint)
    for lbl, r in xt.iterrows():
        md.append(f"| {lbl} | " + " | ".join(str(int(v)) for v in r.values) + " |")
    md += ["", "## Final label distribution", "| label | n |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in lab.label_final.value_counts().items()]
    md += ["", "## Coder A × coder B (joint labels)", "", "```", ct.to_string(), "```"]

    # ---------------- blind third-model audit (optional) ----------------
    audit_path, design_path = OUT / "audit_blind.jsonl", ANN / "audit_design.csv"
    if audit_path.exists() and design_path.exists():
        design = pd.read_csv(design_path).set_index("id")
        aud, pr = load_coder(audit_path, list(design.index))
        if pr:
            print("AUDIT PROBLEMS:", pr)
            return 1
        ja_aud = pd.Series([joint_label(x, y) for x, y in zip(aud.is_complaint, aud.category)], index=aud.index)
        res = {}
        for name, mask in (("disagreements", design.disagree), ("agreed", ~design.disagree)):
            ids = design.index[mask]
            j = ja_aud[ids]
            res[name] = {"n": int(len(ids)),
                         "auditor_vs_final": float((j == lab.label_final[ids]).mean()),
                         "auditor_vs_A": float((j == lab.label_a[ids]).mean()),
                         "auditor_vs_B": float((j == lab.label_b[ids]).mean()),
                         "auditor_vs_final_complaint_only": float(
                             (aud.is_complaint[ids] == lab.is_complaint[ids]).mean())}
        stats["blind_audit"] = res
        (ML / "results" / "agreement.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
        md += ["", "## Blind third-model audit",
               "A third model (Claude Opus, the session's default model) relabelled 180 items **blind** (text + guide only): "
               "120 random A/B disagreements and 60 random agreed items (`data/annotation/audit_design.csv`). "
               "It measures how often an independent coder reproduces the reference label.",
               "", "| subset | n | audit = final | audit = coder A | audit = coder B | audit = final (complaint yes/no/unclear only) |",
               "|---|---|---|---|---|---|"]
        for name, r in res.items():
            md.append(f"| {name} | {r['n']} | {r['auditor_vs_final']:.3f} | {r['auditor_vs_A']:.3f} | {r['auditor_vs_B']:.3f} | "
                      f"{r['auditor_vs_final_complaint_only']:.3f} |")
    rejected = sorted(p.name for p in (OUT / "rejected").glob("*.jsonl")) if (OUT / "rejected").exists() else []
    md += ["", "## Quality incidents (kept for transparency)",
           "- Pilot: coder B's first run produced no labels (it wrote an unrelated plan); it was re-run with a strict labeling-only prompt.",
           "- Batch `main_05`: coder B's first output was degenerate (30 complaints vs 92–124 in every other batch; it missed obvious "
           "complaints such as \"ما يرضى يشتغل\"). It and the adjudication built on it were moved to `out/rejected/`; coder B "
           "re-labelled the batch (prompt with an added reminder that short texts can report concrete problems) and it was re-adjudicated.",
           f"- Rejected files: {', '.join(rejected) or 'none'}"]
    (ML / "reports" / "agreement.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: stats[k] for k in ("overall", "n_adjudicated", "final_distribution")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
