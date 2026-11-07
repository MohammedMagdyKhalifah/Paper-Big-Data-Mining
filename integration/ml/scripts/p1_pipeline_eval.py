"""P1.4 end-to-end checks of ml.analyze with the real MARBERT export (a4-marbert-v1) and the default OCR engine.

Usage (from this ml/ dir):
  ML_ARTIFACT_DIR=$PWD/artifacts/a4/export/a4-marbert-v1 PYTHONPATH=.. .venv/bin/python scripts/p1_pipeline_eval.py
Writes results/p1/pipeline_eval.json and tests/fixtures/p1/sample_outputs.json.
  (1) OCR -> classification consistency on the synthetic screenshots: predict_text(reference text) vs the
      prediction from analyze(image) (same model; differences are caused by OCR errors only). No labels used.
  (2) analysis_kind per screenshot kind (error screens vs chats/reviews vs no-text).
  (3) a fixed scenario suite (text, mixed, negated/historical, unknown/multiple systems, OCR failures).
  (4) cost: warm-up time, per-stage latency, peak RSS of one process holding OCR + MARBERT.
  (5) error-screen rule on REAL user texts: share of 2,000 random deduplicated AURA reviews that would be flagged
      error_screen_signal if they arrived as image-only OCR text (cues present, no narrative marker). These are
      user reviews, so every flag is a false error-screen flag. Independent of the rule's development data.
"""
import io
import json
import os
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

import pandas as pd

from ml.analyze import analyze, error_cues, narrative_markers, warmup
from ml.infer import predict_text

ML = Path(__file__).resolve().parents[1]
SYN = ML / "data/ocr_eval/synthetic"
FIX = ML / "tests/fixtures/p1"

SCENARIOS = [
    ("arabic_text_auth", dict(text="رمز التحقق ما يوصلني على الجوال وما أقدر أسجل دخول")),
    ("arabic_text_praise", dict(text="تطبيق رائع وسهل الاستخدام شكراً لكم")),
    ("mixed_ar_en", dict(text="الـ OTP ما يوصلني when I try to login في تطبيق Absher")),
    ("negated_problem", dict(text="ما فيه أي مشكلة في الدفع، كل شيء تمام")),
    ("historical_resolved", dict(text="كانت عندي مشكلة في الدخول على تطبيق صحتي بس انحلت بعد التحديث، شكراً")),
    ("ordinary_word_not_system", dict(text="ابشر يا أخوي، توكلنا على الله والتطبيق صار أسرع")),
    ("unknown_system", dict(text="تطبيق سهل للمواصلات يطلع لي خطأ كل ما أحاول أدفع")),
    ("multiple_systems", dict(text="منصة ناجز تطلب التحقق عن طريق النفاذ الوطني الموحد وتطبيق نفاذ ما يفتح")),
    ("error_screen_image_only", dict(image="err00.png")),
    ("error_screen_with_user_text", dict(text="من أمس ما أقدر أجدد الهوية", image="err00.png")),
    ("english_error_image", dict(image="err06.png")),
    ("complaint_chat_image", dict(image="chat03.png")),
    ("degraded_jpeg_image", dict(image="chat05_degraded.jpg")),
    ("no_text_image", dict(image="notext0.png")),
    ("corrupt_image", dict(image="corrupt.png")),
    ("unsupported_gif", dict(image="tiny.gif")),
    ("ocr_corrected_text", dict(image="err03.png", corrected_text="منصة نفاذ: رمز التحقق غير صحيح")),
]


def make_fixtures():
    FIX.mkdir(parents=True, exist_ok=True)
    for f in ("err00.png", "err03.png", "err06.png", "chat03.png", "chat05_degraded.jpg", "notext0.png"):
        (FIX / f).write_bytes((SYN / "images" / f).read_bytes())
    (FIX / "corrupt.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, format="GIF")
    (FIX / "tiny.gif").write_bytes(buf.getvalue())


def main():
    if "ML_ARTIFACT_DIR" not in os.environ:
        raise SystemExit("set ML_ARTIFACT_DIR to the a4-marbert-v1 export")
    make_fixtures()
    w = warmup()
    rows = [json.loads(l) for l in (SYN / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    per, kinds, lat = [], defaultdict(Counter), defaultdict(list)
    for r in rows:
        a = analyze(image=SYN / r["file"])
        kinds[r["kind"]][a["analysis_kind"]] += 1
        for k, v in a["timing_ms"].items():
            lat[k].append(v)
        if r["kind"] == "no_text":
            continue
        ref = predict_text(r["reference_text"])
        p = a["prediction"] or {}
        per.append({"file": r["file"], "variant": r["variant"], "kind": r["kind"],
                    "same_is_complaint": p.get("is_complaint") == ref["is_complaint"],
                    "same_category": p.get("category") == ref["category"],
                    "same_needs_review": p.get("needs_review") == ref["needs_review"],
                    "abs_diff_complaint_score": round(abs(p.get("complaint_score", 0) - ref["complaint_score"]), 4)})
    by_v = defaultdict(list)
    for x in per:
        by_v[x["variant"]].append(x)
    cons = {v: {"n": len(xs), "same_is_complaint": round(sum(x["same_is_complaint"] for x in xs) / len(xs), 4),
                "same_category": round(sum(x["same_category"] for x in xs) / len(xs), 4),
                "same_needs_review": round(sum(x["same_needs_review"] for x in xs) / len(xs), 4),
                "max_abs_diff_complaint_score": max(x["abs_diff_complaint_score"] for x in xs)}
            for v, xs in sorted(by_v.items())}
    scen = {}
    for name, kw in SCENARIOS:
        kw = {k: (FIX / v if k == "image" else v) for k, v in kw.items()}
        a = analyze(**kw)
        a["ocr"] = a["ocr"] and {k: v for k, v in a["ocr"].items() if k != "lines"}  # keep fixture compact
        a.pop("timing_ms")
        scen[name] = {"input": {k: (str(Path(v).name) if k == "image" else v) for k, v in kw.items()}, "output": a}
    corpus = pd.read_parquet(ML / "data/interim/corpus.parquet")
    real = corpus[corpus.exclusion_reason.isna()].drop_duplicates("dup_group").sample(2000, random_state=2032).text_p0.tolist()
    with_cue = [t for t in real if error_cues(t)]
    flagged = [t for t in with_cue if not narrative_markers(t)]
    real_check = {"n_reviews": len(real), "with_error_cue": len(with_cue), "flagged_error_screen": len(flagged),
                  "false_flag_rate": round(len(flagged) / len(real), 4),
                  "false_flag_rate_among_cue_texts": round(len(flagged) / max(1, len(with_cue)), 4),
                  "examples_flagged": flagged[:8]}
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))]
    out = {"model_version": w["model_version"], "ocr_engine": w["ocr_engine"], "warmup_s": w["elapsed_s"],
           "synthetic_images": len(rows), "consistency_ocr_vs_reference_text": cons,
           "analysis_kind_by_screenshot_kind": {k: dict(v) for k, v in kinds.items()},
           "latency_ms": {k: {"mean": round(sum(v) / len(v), 1), "p50": q(v, .5), "p95": q(v, .95)} for k, v in lat.items()},
           "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 1), "device": "CPU (Apple M2 Max)",
           "error_screen_rule_on_real_reviews": real_check,
           "scenarios": {k: {"analysis_kind": v["output"]["analysis_kind"], "prediction": v["output"]["prediction"],
                             "systems_status": v["output"]["systems"] and v["output"]["systems"]["status"],
                             "systems": v["output"]["systems"] and [s["system_id"] for s in v["output"]["systems"]["systems"]],
                             "possible": v["output"]["systems"] and [p["system_id"] for p in v["output"]["systems"]["possible_mentions"]],
                             "ocr_status": v["output"]["ocr"] and v["output"]["ocr"]["status"],
                             "error_cues": [c["cue"] for c in v["output"]["signals"]["error_message_cues"]]} for k, v in scen.items()}}
    (ML / "results/p1/pipeline_eval.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    (FIX / "sample_outputs.json").write_text(json.dumps(scen, indent=2, ensure_ascii=False))
    print(json.dumps({k: out[k] for k in ("warmup_s", "consistency_ocr_vs_reference_text", "analysis_kind_by_screenshot_kind", "latency_ms", "peak_rss_mb", "error_screen_rule_on_real_reviews")}, indent=1, ensure_ascii=False))
    for k, v in out["scenarios"].items():
        print(k, v["analysis_kind"], v["prediction"] and (v["prediction"]["is_complaint"], v["prediction"]["category"], v["prediction"]["needs_review"]), v["systems_status"], v["systems"], v["possible"], v["ocr_status"])


if __name__ == "__main__":
    main()
