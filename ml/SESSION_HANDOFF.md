# Session Handoff — `ml/`

**Recovery protocol:** read `../CLAUDE_CODE_ML_RESEARCH_PLAN.md`, then `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, this file, then check the real state (`git log`, `cd ml && .venv/bin/pytest -q`). Trust code and tests over these docs if they conflict.

## Status
**P0 (A0–A2) complete and verified. A3.1 K-Means done.** Model `tfidf-baseline-v1` is trained, exported, and evaluated once on test.
Last verified step: `pytest -q` gives 20 passed; `evaluate.py` rerun gives "REPRODUCTION CHECK: identical metrics".
Active task: none. Waiting for the owner's decision on A3.2 (MARBERT), which is BLOCKED.

## Key decisions
- Only `ml/` (its own git repo, branch `agent/claude-ml`). Codex owns `app/`. Contract unchanged.
- Data: AURA-Sentiment + AURA-Cls v2 (MIT, pinned revisions). 2,000-item sample, 1,000 of them gov apps, games excluded.
- Labels: AI-assisted (A = sonnet, B = haiku, adjudicator = sonnet) + blind Opus audit. Reported honestly as not human gold.
- AURA-Cls human labels are never used for training; they are the external check.
- Selected: P1 + char_wb(2–5) TF-IDF; gate LR C=10 balanced; category calibrated LR C=1 balanced.
- The test split was used once (2026-10-29). **Do not tune on test.** Reruns are reproduction checks only.

## Locations
- Artifacts: `artifacts/gate.joblib`, `artifacts/category.joblib` (gitignored, rebuild with `train.py`), `artifacts/manifest.json`
- Labels: `data/annotation/labels.parquet`. Coder outputs: `data/annotation/out/` (rejected ones in `out/rejected/`)
- Split: `data/splits/split_manifest.csv` (sha 451ab15d…)
- Results: `results/{test_metrics.json, experiment_register.csv, agreement.json, kmeans.json, confusion_category_test.*, errors_category_test.csv}`
- Reports: `reports/{data_manifest, annotation_guide, agreement, evaluation, model_card, clustering, integration_notes}.md`

## Commands (from repo root `Project/`)
```bash
PYTHONPATH=. ml/.venv/bin/python -c 'from ml.infer import predict_text; print(predict_text("التطبيق بطيء"))'
PYTHONPATH=. ml/.venv/bin/python ml/scripts/train.py      # rebuild artifacts (deterministic)
PYTHONPATH=. ml/.venv/bin/python ml/scripts/evaluate.py   # reproduction check
cd ml && .venv/bin/pytest -q
```

## Known problems
- TRANS recall 0.125 (n=8 test), UX recall 0.36. Some confident misses on mixed-language and UX phrasing.
- No dates in AURA. Labels are AI-assisted. Generalisation to e-mail/OCR is untested.

## Exact next action
Ask the owner whether to (a) run ONE MARBERT fine-tune on MPS (A3.2) using the same split, compared on val then test once as a new model version, or (b) stop at P0. Do not start without approval.
