"""Draw the P1 system-mention evaluation sample from the AURA corpus (after registry v1 was frozen).

Usage (from this ml/ dir):  PYTHONPATH=.. .venv/bin/python scripts/p1_mention_sample.py
Pool = deduplicated, non-excluded corpus records (one per dup_group), PII-masked text_p0.
  stratum "name_hit": text contains a registry name/alias as a loose normalised substring (no boundary/context
                      rules) -> up to 12 per system, sampled at random  (precision + ambiguity behaviour)
  stratum "gov_app_no_hit": reviews of registry gov apps with no substring hit -> 100 at random (missed mentions)
Writes data/p1/mentions/sample.jsonl (id, text, stratum, hidden fields) and coder_items.jsonl (id, text only).
"""
import json
import random
from pathlib import Path

import pandas as pd
import yaml

from ml.src.systems import norm

ML = Path(__file__).resolve().parents[1]
SEED = 2031
OUT = ML / "data/p1/mentions"
GOV_APPS = {"Absher": "absher", "Tawakkalna": "tawakkalna", "Sehhaty": "sehhaty", "Mawid": "mawid", "Madrasati": "madrasati",
            "Tabaud": "tabaud", "Tetamman": "tetamman", "Asefni": "asefni", "Eatmarna": "eatmarna", "Kollona Amn": "kollona_amn",
            "Citizen Account": "citizen_account", "Taminati": "taminati", "Saudi Post": "saudi_post", "Sakani": "sakani",
            "Mawared": "mawared", "Watani": "watani", "Balady": "balady", "MOJ": "najiz"}


def main():
    reg = yaml.safe_load((ML / "configs/systems.yaml").read_text(encoding="utf-8"))
    names = [(s["id"], norm(a)) for s in reg["systems"] for a in s.get("aliases", []) + s.get("ambiguous", [])]
    c = pd.read_parquet(ML / "data/interim/corpus.parquet")
    c = c[c.exclusion_reason.isna()].drop_duplicates("dup_group")
    c = c.assign(nt=c.text_p0.map(norm))
    c["hits"] = c.nt.map(lambda t: sorted({sid for sid, a in names if a in t}))
    rng = random.Random(SEED)
    rows = []
    for sid in [s["id"] for s in reg["systems"]]:
        sub = c[c.hits.map(lambda h: sid in h) & ~c.record_id.isin([r["record_id"] for r in rows])]
        for r in sub.sample(min(12, len(sub)), random_state=rng.randint(0, 10**6)).itertuples():
            rows.append({"record_id": r.record_id, "stratum": "name_hit", "drawn_for": sid, "app_canonical": r.app_canonical, "text": r.text_p0})
    nohit = c[(c.hits.map(len) == 0) & c.app_canonical.isin(GOV_APPS)]
    for r in nohit.sample(100, random_state=SEED).itertuples():
        rows.append({"record_id": r.record_id, "stratum": "gov_app_no_hit", "drawn_for": None, "app_canonical": r.app_canonical, "text": r.text_p0})
    rng.shuffle(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(rows):
        r["id"] = f"m{i:04d}"
    with open(OUT / "sample.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT / "coder_items.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], "text": r["text"]}, ensure_ascii=False) + "\n")
    print(len(rows), pd.Series([r["stratum"] for r in rows]).value_counts().to_dict(),
          pd.Series([r["drawn_for"] for r in rows if r["drawn_for"]]).value_counts().to_dict())


if __name__ == "__main__":
    main()
