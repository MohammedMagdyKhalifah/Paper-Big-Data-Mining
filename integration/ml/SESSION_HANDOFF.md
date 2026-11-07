# Session Handoff — `ml/`

**Recovery:** read `../CLAUDE_CODE_ML_RESEARCH_PLAN.md`, `IMPLEMENTATION_PLAN.md` (§A4, §P1), `PROGRESS.md`, then check git in each worktree. Trust code over docs.

## Status
- v1 `tfidf-baseline-v1` is the default, used by Codex from the main tree `ml/` (branch `agent/claude-ml`). Untouched.
- **A4 complete** (worktree `ml/.worktrees/a4/ml`, branch `agent/claude-ml-a4`): `a4-marbert-v1`, opt-in via `ML_ARTIFACT_DIR`, not auto-promoted. Do not re-tune on the holdout.
- **P1 complete** (worktree `ml/.worktrees/p1/ml`, branch `agent/claude-ml-p1`, based on A4): `ml.analyze.analyze()` (OCR + unchanged `predict_text` + system names + error-screen signal), `ml.src.ocr`, `ml.src.systems`. See `reports/p1_report.md` and `reports/p1_integration_notes.md`.

## Commands (P1 worktree)
```bash
HF_HUB_OFFLINE=1 .venv/bin/pytest -q
ML_ARTIFACT_DIR=$PWD/artifacts/a4/export/a4-marbert-v1 PYTHONPATH=.. .venv/bin/python scripts/p1_pipeline_eval.py
PYTHONPATH=.. .venv/bin/python scripts/p1_mention_eval.py   # registry metrics (v1 file = unbiased)
```

## Next (owner decisions)
1. Promote a4-marbert-v1 and merge `agent/claude-ml-p1` (contains A4) for Codex. Codex adds `requirements-p1.txt` to the app env.
2. Test OCR on a few REAL screenshots (`data/ocr_eval/real/`). Current numbers are synthetic only.
3. Extend `configs/systems.yaml` to non-gov services if needed (no retraining).
4. Still open from A4: a human spot-check, and PERF being small.
