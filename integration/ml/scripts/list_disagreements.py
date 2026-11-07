"""Print the items of one batch on which coder A and coder B disagree (for the adjudicator).

Usage: ml/.venv/bin/python ml/scripts/list_disagreements.py <batch>     e.g. main_03
Prints one JSON object per disagreement: {id, text, coder_A, coder_B}; last line: {"n_disagreements": N}.
Exits non-zero if either coder file is missing or incomplete.
"""
import json
import sys
from pathlib import Path

ML = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML.parent))
from ml.src.agreement import joint_label, load_coder  # noqa: E402


def main(batch: str) -> int:
    rows = [json.loads(l) for l in (ML / "data/annotation/batches" / f"{batch}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = [r["id"] for r in rows]
    a, pa = load_coder(ML / "data/annotation/out" / f"coderA_{batch}.jsonl", ids)
    b, pb = load_coder(ML / "data/annotation/out" / f"coderB_{batch}.jsonl", ids)
    if pa or pb:
        print(json.dumps({"error": pa + pb}, ensure_ascii=False))
        return 1
    n = 0
    for r in rows:
        ra, rb = a.loc[r["id"]], b.loc[r["id"]]
        if joint_label(ra.is_complaint, ra.category) != joint_label(rb.is_complaint, rb.category):
            n += 1
            fmt = lambda x: {"is_complaint": x.is_complaint, "category": x.category}
            print(json.dumps({"id": r["id"], "text": r["text"], "coder_A": fmt(ra), "coder_B": fmt(rb)}, ensure_ascii=False))
    print(json.dumps({"n_disagreements": n}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
