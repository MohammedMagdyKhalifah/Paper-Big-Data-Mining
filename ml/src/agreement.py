"""Load/validate coder outputs and compute agreement (inter-AI-annotator, plus AURA human proxy)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

CATS = ["AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER"]
COMPLAINT = ["yes", "no", "unclear"]


def load_coder(path: Path, expected_ids: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Return (labels, problems). Problems lists invalid/missing/duplicate rows (never silently fixed)."""
    rows, problems = [], []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"{path.name}:{n} invalid JSON")
            continue
        ic, cat = r.get("is_complaint"), r.get("category")
        if ic not in COMPLAINT:
            problems.append(f"{r.get('id')}: bad is_complaint={ic!r}")
            continue
        if ic == "yes" and cat not in CATS:
            problems.append(f"{r.get('id')}: complaint without valid category ({cat!r})")
            continue
        if ic != "yes" and cat is not None:
            problems.append(f"{r.get('id')}: category {cat!r} on non-complaint (set to null)")
            cat = None
        rows.append({"id": r.get("id"), "is_complaint": ic, "category": cat,
                     "multi_issue": bool(r.get("multi_issue")), "negation": bool(r.get("negation")),
                     "uncertain": bool(r.get("uncertain"))})
    df = pd.DataFrame(rows)
    if df.empty:
        return df, problems + ["no rows"]
    dup = df.id[df.id.duplicated()].tolist()
    if dup:
        problems.append(f"duplicate ids: {dup[:10]}")
        df = df.drop_duplicates("id", keep="first")
    missing = sorted(set(expected_ids) - set(df.id))
    extra = sorted(set(df.id) - set(expected_ids))
    if missing:
        problems.append(f"missing {len(missing)} ids: {missing[:10]}")
    if extra:
        problems.append(f"unexpected ids: {extra[:10]}")
        df = df[~df.id.isin(extra)]
    return df.set_index("id"), problems


def joint_label(ic: str, cat) -> str:
    """8-way label used for overall agreement: a category, NO, or UNCLEAR."""
    return cat if ic == "yes" else ic.upper()


def agreement(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    ids = a.index.intersection(b.index)
    a, b = a.loc[ids], b.loc[ids]
    ja = [joint_label(x, y) for x, y in zip(a.is_complaint, a.category)]
    jb = [joint_label(x, y) for x, y in zip(b.is_complaint, b.category)]
    both_yes = (a.is_complaint == "yes") & (b.is_complaint == "yes")
    out = {
        "n": int(len(ids)),
        "complaint_pct_agree": float((a.is_complaint == b.is_complaint).mean()),
        "complaint_kappa": float(cohen_kappa_score(a.is_complaint, b.is_complaint)),
        "joint_pct_agree": float(pd.Series(ja).eq(pd.Series(jb)).mean()),
        "joint_kappa": float(cohen_kappa_score(ja, jb)),
        "category_n_both_yes": int(both_yes.sum()),
    }
    if both_yes.sum() > 1:
        out["category_pct_agree"] = float((a.category[both_yes] == b.category[both_yes]).mean())
        out["category_kappa"] = float(cohen_kappa_score(a.category[both_yes], b.category[both_yes]))
    return out


def crosstab(a: pd.Series, b: pd.Series, labels) -> pd.DataFrame:
    m = confusion_matrix(a, b, labels=labels)
    return pd.DataFrame(m, index=[f"A:{x}" for x in labels], columns=[f"B:{x}" for x in labels])
