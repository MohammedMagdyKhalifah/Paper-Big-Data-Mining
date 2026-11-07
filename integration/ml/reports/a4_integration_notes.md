# A4 Integration Notes (for Codex / owner)

- **Default unchanged:** `ml.infer.predict_text` with no env var still serves `tfidf-baseline-v1` from `ml/artifacts` (main tree, branch `agent/claude-ml`). Nothing in `app/` needs to change.
- **Candidate model:** `a4-marbert-v1` (MARBERTv2 7-way, fine-tuned with synthetic augmentation). Artifact: `ml/.worktrees/a4/ml/artifacts/a4/export/a4-marbert-v1/` (fp16 weights, 328 MB, gitignored; rebuild with `scripts/a4_experiments.py marbert_seeds --synthetic` then `a4_select.py`).
- **Opt-in:** `ML_ARTIFACT_DIR=<that dir>` with the A4 branch's `infer.py` (backend `hf-7way`). The contract is identical (same 6 keys and types). It needs `torch` + `transformers` (see `.venv`). It runs offline on CPU (`HF_HUB_OFFLINE=1` is set internally): first call about 3 s, then about 34 ms/message, peak RSS about 1.5 GB.
- **Not auto-promoted.** Replacing the default requires the owner's decision and merging `agent/claude-ml-a4`.
- `needs_review`: gate never flagged (validation showed ≥90% precision at full coverage); category flagged when category_score < 0.90. On the holdout, 27% of messages are flagged; automatic decisions are 91% accurate.

## Handoff checklist for promoting `a4-marbert-v1`
1. **Artifacts:** `artifacts/a4/export/a4-marbert-v1/{manifest.json, SHA256SUMS, model/}`. Verify with `cd artifacts/a4/export/a4-marbert-v1 && shasum -a 256 -c SHA256SUMS`. `model/model.safetensors` (fp16, sha256 prefix `492b0585b9310e6e`) is gitignored. Copy it with the folder, or rebuild deterministically from the code at commit `2b15bc4` (see the README section below).
2. **Dependencies** (exact, CPU inference): `requirements-a4-inference.txt` (torch 2.15.0, transformers 5.22.0, tokenizers 0.23.3, safetensors 0.8.0, scikit-learn 1.9.1, …). The v1 default needs only the sklearn subset.
3. **Code:** merge branch `agent/claude-ml-a4` into `agent/claude-ml` (adds the `hf-7way` backend in `infer.py` plus `src/hf_model.py` and `src/a4_common.py`). Without an env var the default stays v1.
4. **Switch:** set `ML_ARTIFACT_DIR=<abs path>/artifacts/a4/export/a4-marbert-v1` in the app environment. Rollback = unset it.
5. **Contract:** unchanged keys and types. `model_version` becomes `a4-marbert-v1`; the app should store it per prediction (it already does).
6. **Runtime expectations:** first call about 3 s (model load), then about 34 ms/message on CPU, peak RSS about 1.5 GB. Keep one process-wide model (already cached in `ml.infer`).
7. **Tests to run after integrating:** `HF_HUB_OFFLINE=1 .venv/bin/pytest -q tests/test_contract.py tests/test_a4.py tests/test_a4_export_integrity.py`.

Rebuild (only if the weights are lost): `PYTHONPATH=.. HF_HUB_OFFLINE=1 .venv/bin/python scripts/a4_experiments.py marbert_seeds --synthetic --seeds 42`, then `scripts/a4_select.py`. MPS training is not bit-exact, so a rebuilt model must be re-validated (val only); the holdout must not be re-used for selection.
