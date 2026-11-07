"""Print anonymised disagreements between two label files of one A4 batch (for the adjudicator).

Usage: .venv/bin/python scripts/a4_list_disagreements.py <batch> [coderX] [coderY]     (defaults: coderA coderB)
Reads data/a4/batches/<batch>.jsonl and data/a4/out/<coder>_<batch>.jsonl.
Labels are shown as "label_1"/"label_2" in an order that is shuffled per item (hash of id), so the adjudicator
cannot tell which model produced which label. Last line: {"n_disagreements": N}. Non-zero exit if files are incomplete.
"""
import hashlib
import json
import sys
from pathlib import Path

ML = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML.parent))
from ml.src.agreement import joint_label, load_coder  # noqa: E402


def main(batch, cx="coderA", cy="coderB") -> int:
    rows = [json.loads(l) for l in (ML / "data/a4/batches" / f"{batch}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = [r["id"] for r in rows]
    x, px = load_coder(ML / "data/a4/out" / f"{cx}_{batch}.jsonl", ids)
    y, py = load_coder(ML / "data/a4/out" / f"{cy}_{batch}.jsonl", ids)
    if px or py:
        print(json.dumps({"error": px + py}, ensure_ascii=False))
        return 1
    n = 0
    for r in rows:
        a, b = x.loc[r["id"]], y.loc[r["id"]]
        if joint_label(a.is_complaint, a.category) == joint_label(b.is_complaint, b.category):
            continue
        n += 1
        la, lb = ({"is_complaint": a.is_complaint, "category": a.category},
                  {"is_complaint": b.is_complaint, "category": b.category})
        if int(hashlib.sha1(r["id"].encode()).hexdigest(), 16) % 2:
            la, lb = lb, la
        print(json.dumps({"id": r["id"], "text": r["text"], "label_1": la, "label_2": lb}, ensure_ascii=False))
    print(json.dumps({"n_disagreements": n}))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
