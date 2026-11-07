# `ml/`: Arabic technical-complaint detection and categorisation (local)

Owner: Claude Code. Consumed by `app/` (Codex) only through `ml.infer.predict_text`.

## Use (from the repository root)
```bash
PYTHONPATH=. ml/.venv/bin/python -c 'from ml.infer import predict_text; print(predict_text("التطبيق بطيء"))'
```
`predict_text(text: str) -> dict` returns exactly these keys:
`is_complaint` (bool), `complaint_score` (float 0–1), `category` (`AUTH|AVAIL|PERF|TRANS|UX|OTHER` or `None`), `category_score` (float 0–1 or `None`), `needs_review` (bool), `model_version` (str).
- Empty or whitespace input raises `ValueError`. A non-str input raises `TypeError`. Missing artifacts raise `FileNotFoundError` (there is never mock output).
- The model loads once per process, runs fully offline, and needs only `scikit-learn`, `numpy`, `scipy`, and `joblib`.
- Score meaning and thresholds are in `reports/model_card.md` and `artifacts/manifest.json`.

## Setup
```bash
cd ml && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Reproduce everything (from the repository root)
```bash
PYTHONPATH=. ml/.venv/bin/python ml/scripts/download_data.py     # AURA datasets, pinned HF revisions + sha256
PYTHONPATH=. ml/.venv/bin/python ml/scripts/prepare_data.py      # cleaning, PII masking, dedup groups, annotation sample
# annotation: coder outputs live in ml/data/annotation/out/ (see reports/agreement.md for provenance)
PYTHONPATH=. ml/.venv/bin/python ml/scripts/build_labels.py      # merge coders + adjudication -> labels.parquet, agreement report
PYTHONPATH=. ml/.venv/bin/python ml/scripts/make_split.py        # frozen group-aware 70/15/15 split (refuses to change silently)
PYTHONPATH=. ml/.venv/bin/python ml/scripts/train.py             # grid on train/val only -> artifacts/
PYTHONPATH=. ml/.venv/bin/python ml/scripts/evaluate.py          # held-out test; later runs = reproduction check
cd ml && .venv/bin/pytest -q                                      # contract, text, leakage tests
```

## Layout
| path | content |
|---|---|
| `infer.py` | frozen inference contract |
| `src/text.py` | PII masking, P0/P1 normalisation (negations kept) |
| `src/dedup.py` | exact + near-duplicate groups |
| `src/models.py` | pipelines (TF-IDF + LR / calibrated LR / calibrated LinearSVC) |
| `src/split.py`, `src/agreement.py` | split and agreement utilities |
| `configs/` | taxonomy, app→domain mapping |
| `data/` | raw/interim (local, gitignored), annotation sample/batches/outputs, split manifest |
| `artifacts/` | `gate.joblib`, `category.joblib` (gitignored), `manifest.json` |
| `results/` | experiment register, test metrics, confusion matrices, errors |
| `reports/` | data manifest, annotation guide, agreement, evaluation, model card, integration notes |
| `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, `SESSION_HANDOFF.md` | plan, log, recovery |
