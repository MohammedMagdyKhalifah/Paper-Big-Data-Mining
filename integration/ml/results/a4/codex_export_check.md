# A4 export integrity check

Date: 2026-10-30

Export: `artifacts/a4/export/a4-marbert-v1/`

Test module: `tests/test_a4_export_integrity.py`

## Execution and result

Ran from the requested git worktree:

```sh
HF_HUB_OFFLINE=1 .venv/bin/pytest -q tests/test_a4_export_integrity.py
```

Result: **12 passed in 7.98s**, exit code **0**. No test failures or warnings were reported. No test corrections or reruns were needed.

The shell also set `PYTHONDONTWRITEBYTECODE=1` and `PYTEST_ADDOPTS='-p no:cacheprovider'` to prevent bytecode and pytest cache writes. No other tests or project scripts were run.

## Verified

- All six entries in `SHA256SUMS` matched the actual SHA-256 digests: `manifest.json`, `model/a4_meta.json`, `model/config.json`, `model/model.safetensors`, `model/tokenizer.json`, and `model/tokenizer_config.json`. The test also rejects empty checksum lists, malformed lines, duplicate entries, missing files, and paths escaping the export.
- The manifest declares `model_version="a4-marbert-v1"`, `backend="hf-7way"`, and an existing `files.model_dir`. All four required thresholds are numeric and within `[0, 1.01]`: `gate_decision=0.5`, `gate_review_low=0.5`, `gate_review_high=0.5`, and `category_review=0.9`.
- `model/config.json` maps label IDs 0–6 to `NO, AUTH, AVAIL, PERF, TRANS, UX, OTHER`, in that order, with no extra IDs.
- With `ML_ARTIFACT_DIR` pointing to the export and `HF_HUB_OFFLINE=1`, five short Arabic/mixed-language probes returned exactly `is_complaint`, `complaint_score`, `category`, `category_score`, `needs_review`, and `model_version`. Types, score bounds, version, category membership, and null category/category score for non-complaints passed.
- Three whitespace-only inputs (ordinary spaces, tabs/newlines, and Unicode spaces) raised `ValueError`.
- A separate `ml.src.hf_model.HFPredictor(export / "model")` produced finite, normalized probabilities of shape `(5, 7)`. For every probe, `complaint_score` exactly matched `round(float(1 - P[i, 0]), 4)`; every complaint category matched the argmax over `P[i, 1:]`.
- Repeating all five predictions preserved both their results and the identity of `ml.infer._model`.

The five synthetic probes were:

1. `رمز التحقق لا يصل عند تسجيل الدخول`
2. `تطبيق رائع وسهل الاستخدام شكرا لكم`
3. `الـ OTP ما يوصلني when I try to login`
4. `التطبيق بطيء جدا والصفحة تحمل وقت طويل`
5. `الدفع fails عند تأكيد العملية`

## Isolation and problems

The module has a module-wide skip condition naming the missing weights path when `model/model.safetensors` is absent. Weights were present during this run, so all tests executed; the missing-weights condition was not simulated.

A module-scoped fixture uses `pytest.MonkeyPatch.context()` to restore `ML_ARTIFACT_DIR`, `HF_HUB_OFFLINE`, and `TOKENIZERS_PARALLELISM`, and calls `ml.infer._reset_cache()` in a `finally` teardown, including after test failures. Imports use the existing parent-directory setup in `tests/conftest.py`.

**Problems found: none.** No artifact or inference changes were needed. Only the requested test module and this report were created. No training, evaluation/selection scripts, holdout-label reads, or git commits were performed.
