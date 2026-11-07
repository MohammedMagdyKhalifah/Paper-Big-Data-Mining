"""Score stored OCR predictions against manifest reference text. Synthetic and real sets are reported separately.

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/p1_ocr_eval.py [--set synthetic]
Writes results/p1/ocr_metrics_<set>.json. Micro-averaged CER/WER (sum of edits / sum of reference length).
No-text images are scored only on whether the engine returned status "empty".
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from ml.src.ocr_metrics import cer_wer, norm_letters, norm_light

ML = Path(__file__).resolve().parents[1]


def agg(rows, norm):
    ce = cn = we = wn = 0
    for r in rows:
        a, b, c, d = cer_wer(r["text"], r["reference_text"], norm)
        ce, cn, we, wn = ce + a, cn + b, we + c, wn + d
    return {"n": len(rows), "cer": round(ce / cn, 4) if cn else None, "wer": round(we / wn, 4) if wn else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="synthetic")
    a = ap.parse_args()
    root = ML / "data/ocr_eval" / a.set
    man = {r["file"]: r for r in map(json.loads, (root / "manifest.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    out = {"set": a.set, "synthetic": all(r["synthetic"] for r in man.values()), "n_images": len(man), "engines": {}}
    for pf in sorted((ML / "results/p1/ocr").glob(f"{a.set}_*.jsonl")):
        name = pf.stem[len(a.set) + 1:]
        preds = [{**man[p["file"]], **p} for p in map(json.loads, pf.read_text(encoding="utf-8").splitlines())]
        text_rows = [p for p in preds if p["kind"] != "no_text"]
        nt = [p for p in preds if p["kind"] == "no_text"]
        e = {"engine": preds[0]["engine"], "all_text_images": {"light": agg(text_rows, norm_light), "letters": agg(text_rows, norm_letters)}}
        for key in ("variant", "kind", "theme", "font"):
            groups = defaultdict(list)
            for p in text_rows:
                groups[p[key]].append(p)
            e[f"by_{key}"] = {g: agg(v, norm_light) for g, v in sorted(groups.items())}
        e["status_counts_text_images"] = {s: sum(p["status"] == s for p in text_rows) for s in ("ok", "empty", "failed")}
        e["no_text_images"] = {"n": len(nt), "returned_empty": sum(p["status"] == "empty" for p in nt),
                               "spurious_text": [p["text"][:60] for p in nt if p["status"] != "empty"]}
        cost = pf.with_name(pf.stem + "_cost.json")
        e["cost"] = json.loads(cost.read_text()) if cost.exists() else None
        out["engines"][name] = e
    (ML / f"results/p1/ocr_metrics_{a.set}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for n, e in out["engines"].items():
        print(n, e["all_text_images"], {k: v["cer"] for k, v in e["by_variant"].items()}, {k: v["cer"] for k, v in e["by_kind"].items()},
              {k: v["cer"] for k, v in e["by_theme"].items()}, e["no_text_images"]["returned_empty"], e["cost"]["latency_ms_mean"])


if __name__ == "__main__":
    main()
