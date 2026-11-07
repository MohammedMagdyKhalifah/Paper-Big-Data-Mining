"""Run one OCR engine over an OCR eval manifest and store raw predictions (no metrics here).

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/p1_ocr_run.py --engine tesseract [--set synthetic]
PaddleOCR:                  PYTHONPATH=.. .venv-paddle/bin/python scripts/p1_ocr_run.py --engine paddle
Writes results/p1/ocr/<set>_<engine>.jsonl and <set>_<engine>_cost.json (first-call load time, per-image latency, peak RSS).
"""
import argparse
import json
import resource
import time
from pathlib import Path

from ml.src.ocr import extract_text, get_engine

ML = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--set", default="synthetic")
    ap.add_argument("--tag", default="", help="suffix for the output name (engine setting variants)")
    a = ap.parse_args()
    root = ML / "data/ocr_eval" / a.set
    rows = [json.loads(l) for l in (root / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    out_dir = ML / "results/p1/ocr"
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    eng = get_engine(a.engine)
    load_s = time.perf_counter() - t0
    preds, lat = [], []
    for r in rows:
        res = extract_text(root / r["file"], engine=a.engine)
        lat.append(res["elapsed_ms"])
        preds.append({"file": r["file"], **{k: res[k] for k in ("status", "text", "mean_confidence", "low_confidence", "error", "engine", "elapsed_ms")},
                      "n_lines": len(res["lines"])})
    with open(out_dir / f"{a.set}_{a.engine}{a.tag}.jsonl", "w", encoding="utf-8") as f:
        for p in preds:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    lat_sorted = sorted(lat)
    cost = {"engine": eng.name, "n_images": len(rows), "engine_load_s": round(load_s, 2),
            "latency_ms_mean": round(sum(lat) / len(lat), 1), "latency_ms_p50": lat_sorted[len(lat) // 2],
            "latency_ms_max": lat_sorted[-1], "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 1),
            "peak_rss_child_mb": round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6, 1),
            "device": "CPU (Apple M2 Max)"}
    (out_dir / f"{a.set}_{a.engine}{a.tag}_cost.json").write_text(json.dumps(cost, indent=2))
    print(json.dumps(cost))


if __name__ == "__main__":
    main()
