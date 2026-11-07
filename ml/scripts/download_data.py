"""Download the pinned AURA datasets (MIT) from Hugging Face and record provenance.

Usage (from repo root):  PYTHONPATH=. ml/.venv/bin/python ml/scripts/download_data.py
Writes ml/data/raw/*.parquet and ml/data/raw/provenance.json
"""
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

ML = Path(__file__).resolve().parents[1]
RAW = ML / "data" / "raw"

SOURCES = {
    "aura_sentiment": {
        "repo": "irfan-ahmad/AURA-Sentiment",
        "revision": "5e3e345845ba361c2ceb701abf3d53989782485d",
        "file": "data/train-00000-of-00001.parquet",
    },
    "aura_classification_v2": {
        "repo": "irfan-ahmad/AURA-Classification",
        "revision": "686a01bab9c9ca45d1605b4aad0cd0a89c3a2286",
        "file": "AURA-Classification-V2.csv",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    prov = {}
    for name, s in SOURCES.items():
        local = Path(hf_hub_download(s["repo"], s["file"], repo_type="dataset", revision=s["revision"]))
        dest = RAW / f"{name}{local.suffix}"
        shutil.copyfile(local, dest)
        df = pd.read_parquet(dest) if dest.suffix == ".parquet" else pd.read_csv(dest)
        prov[name] = {
            **s,
            "license": "MIT",
            "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "local_file": dest.name,
            "sha256": sha256(dest),
            "rows": int(len(df)),
            "columns": list(df.columns),
        }
        print(name, len(df), list(df.columns))
    (RAW / "provenance.json").write_text(json.dumps(prov, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
