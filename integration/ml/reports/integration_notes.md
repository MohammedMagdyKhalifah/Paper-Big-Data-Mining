# Integration Notes (Claude Code → Codex / project owner)

## Contract status: **unchanged**
`ml.infer.predict_text(text: str) -> dict` returns exactly these keys: `is_complaint, complaint_score, category, category_score, needs_review, model_version`, as specified in `CLAUDE_CODE_ML_RESEARCH_PLAN.md` §3. No key was added or removed.
- `complaint_score` and `category_score` are **always numeric** (0–1, rounded to 4 decimals) for a complaint. `category_score` is `None` when `is_complaint=False`.
- `model_version` = `"tfidf-baseline-v1"`.
- Errors: `ValueError` (empty or whitespace), `TypeError` (non-str), `FileNotFoundError` (artifacts missing). There is never mock output.
- The model loads once per process (thread-safe lazy load). Calls after the first take about 1.2 ms.

## Run from the repo root
```bash
PYTHONPATH=. ml/.venv/bin/python -c 'from ml.infer import predict_text; print(predict_text("التطبيق بطيء"))'
# -> {'is_complaint': True, 'complaint_score': 0.9045, 'category': 'PERF', 'category_score': 0.4743, 'needs_review': True, 'model_version': 'tfidf-baseline-v1'}
```
Dependencies at inference time: `scikit-learn==1.9.1`, `numpy`, `scipy`, `joblib` (see `ml/requirements.txt`). The pickled pipelines reference `ml.src.text`, so `ml/` must be importable as a package (`PYTHONPATH=.` from the repo root). Use the **same scikit-learn version**; joblib pickles are not guaranteed across versions.
Optional: `ML_ARTIFACT_DIR=/path` overrides the artifact directory.

## Semantics for the dashboard
- `OTHER` is a real technical-complaint category. Do not merge it with "not complaint" or "needs review".
- `needs_review=True` means the model is not confident (gate band [0.40, 0.60) or category_score < 0.675). On test, 38% of messages were flagged. The unflagged ones were correct 90% of the time.
- The model does **not** detect the system or app name. That is Codex's component.
- The AURA training data has **no dates**. Do not present trends built on AURA records as real time series.

## Deviations from the specification (recorded, not silently applied)
1. **Gold labels (spec §4 A1.7):** the spec requires human Gold Validation/Test. By the project owner's explicit decision, labels were produced by Claude subagents (coder A = Sonnet, coder B = Haiku, adjudicator = Sonnet) and are reported as **AI-assisted reference labels**, never as human gold. Supporting evidence: inter-coder κ 0.78 (complaint) / 0.74 (category); a blind third-model audit reproduced 95% of agreed labels; agreement with **human** AURA `bug_report` labels κ 0.72 (sample) and κ 0.60 for the trained gate on 2,604 unseen items. **Recommendation:** have a human review about 100 test items (e.g. via `data/annotation/labels.parquet`) to quantify human–reference agreement before formal submission.
2. **Gate variant G2** (adding AURA `bug_report` as training data) was not used. AURA-Cls items were kept out of training so they remain a clean external human check.
3. **Category learners are calibrated** (sigmoid) because an uncalibrated LR produced misleading probabilities in a dry run (ECE 0.60).

## Suggestions (no contract change requested)
- Display `complaint_score` and `category_score` as "model confidence", not "accuracy".
- Send `needs_review=True` items to the correction queue. Corrections can later become new training data (no automatic retraining).
