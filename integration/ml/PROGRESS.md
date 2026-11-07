# Progress Log — `ml/`

## 2026-10-29

### Completed (verified)
- **A0.1–A0.3**: skeleton, git repo inside `ml/` on `agent/claude-ml`, `.venv` (Python 3.12.7; scikit-learn 1.9.1, pandas 3.1.0, numpy 2.5.4), `infer.py` contract, tests.
  - Test run: `cd ml && .venv/bin/pytest -q` gave **10 passed, 5 skipped** (5 = real-model tests awaiting artifacts).
  - Fixed one wrong test expectation (collapsing repeated letters turns `أإآ` into `ا` by design).
- **A1.1**: downloaded AURA-Sentiment (rev 5e3e345, 29,700 rows; columns review/appName/platform/sentiment) and AURA-Classification V2 CSV (rev 686a01b, 2,900 rows; label ∈ rating 1298 / bug_report 756 / improvement_request 442 / others 404). MIT on both cards. Neither has a date field.
- **A1.2–A1.5**: `prepare_data.py` run (27 s). Record flow (`reports/record_flow.json`):
  - excluded: 6 not-predominantly-Arabic, 4 too short
  - 29,062 dup groups; 4,998 records in multi-member groups; largest group 465 (formulaic praise); 2,517 near-dup pairs (cos ≥ 0.85). 29.9% of AURA-Cls texts also appear exactly in AURA-Sent; these are grouped together.
  - eligible non-game: 23,584 records → 21,077 unique groups
  - annotation sample of 2,000: gov 1,000 / non-gov 700 / AURA-Cls external 300; sentiment neg 1,275 / pos 427 / n.a. 298
  - Spot-check of near-dup pairs at 0.85–0.88: formulaic variants, so the grouping is conservative (safe for leakage).
- **A1.6**: annotation guide v1.0-draft.

### Files created
`.gitignore, __init__.py, infer.py, requirements.txt, configs/{taxonomy,app_domains}.yaml, src/{text,dedup,agreement}.py, scripts/{download_data,prepare_data}.py, tests/{conftest,test_text,test_contract}.py, reports/{annotation_guide.md,record_flow.json}, data/annotation/{sample.parquet,batches/*.jsonl}`

- **A1.7 pilot** (verified): coder A (sonnet) 100/100 valid. Coder B (haiku) **failed on the first try**: it wrote an unrelated plan and no file. Re-run `wf_2795e900-913` with a strict labeling-only prompt gave 100/100 valid.
  - Pilot agreement A vs B (n=100): complaint κ **0.740** (85% agree), joint 8-way κ **0.669** (76%), category κ **0.692** (n=40 both-yes). 24 disagreements.
  - Haiku overused `unclear` for insults and gibberish. Guide revised and **frozen at v1.0** (rules 8–11 plus `unclear`/`no` clarifications; changelog in the guide).
- Main batches re-cut to 8 × ~238 items (`BATCH_SIZE=238`). Verified that `sample.parquet` and `pilot.jsonl` are identical to the committed versions.
- Scripts written: `scripts/{build_labels,make_split,train,evaluate,list_disagreements}.py`, `src/{split,models,agreement}.py`, `tests/test_leakage.py`, `reports/data_manifest.md`.
- **Dry run** (scratchpad copy, placeholder labels, never used for results) found and fixed 2 problems:
  1. pandas 3 Arrow string arrays break `CalibratedClassifierCV` indexing, so labels are now converted with `.to_numpy(dtype=str)`.
  2. Uncalibrated LR (C=0.1, balanced) gave category ECE 0.60 (misleading scores), so category learners are now **sigmoid-calibrated LR / LinearSVC** (`lr_cal`, `svc`). ECE was 0.11 on the dry run.
  - The full grid trains in about 1 min. `evaluate.py` rerun gives "REPRODUCTION CHECK: identical metrics".

- **A1.8** main labeling `wf_5b278e11-f53`: 25 agents, all files valid. Coder B's `main_05` output was **degenerate** (30 complaints vs 92–124 elsewhere), so it was quarantined in `out/rejected/`. Repair run `wf_a058db9d-5df` re-coded B on main_05 (110 complaints) and re-adjudicated it. The same run did a **blind audit** (Opus, 180 items).
- **Bug fixed:** pandas 3 `groupby.apply` dropped `group_aura_label` in `prepare_data.py`. Fixed with an explicit loop. Regenerated, and verified batches + sample columns byte-identical.
- **A1.9** `build_labels.py` → `labels.parquet`, `reports/agreement.md`:
  - A vs B overall (n=2000): complaint κ **0.781**, joint κ **0.713**, category κ **0.740**. 383 adjudicated (19.1%).
  - AI vs **AURA human** bug_report (n=293): agreement 0.884, κ **0.722**.
  - Blind audit: agreed items 95.0% reproduced; disagreements: audit = final 0.800, = A 0.775, = B 0.158.
  - Final: NO 1122, AVAIL 259, OTHER 221, AUTH 194, UX 79, TRANS 49, UNCLEAR 40, PERF 36.
- **A1.10** split frozen: sha `451ab15d…`, train 1399 / val 300 / test 301. `make_split.py` rerun reports "already frozen and reproducible". Leakage tests 5/5 pass.
- **A2** `train.py` (82 s): gate = P1 char_wb2-5 LR C=10 bal (val 0.875 vs Dummy 0.365); category = P1 char_wb2-5 calibrated LR C=1 bal (val 0.600 vs Dummy 0.079). Thresholds: gate band [0.40, 0.60), category_review 0.675.
- **A2.5** `evaluate.py` run ONCE, then the rerun printed "REPRODUCTION CHECK: identical metrics". **Test:**
  - gate macro-F1 **0.845** (CI 0.801–0.884) vs Dummy 0.363
  - category macro-F1 **0.568** (CI 0.454–0.659) vs Dummy 0.078. Per-class F1: AUTH .77, AVAIL .81, PERF .67 (n=6), OTHER .53, UX .44, TRANS .18 (n=8)
  - end-to-end macro-F1 0.553, accuracy 0.736. 38% needs_review; unflagged accuracy 0.896
  - gate vs AURA human labels, 2,604 unseen items: agreement 0.836, κ 0.604
  - latency 1.2 ms/message
- **Tests:** `pytest -q` gives **20 passed** (contract incl. real AUTH/PERF/non-complaint/mixed/repeat, text, leakage).
- Probes reveal misses: "الـ OTP ما يوصلني when I try to login" → not complaint (0.32); "ما أقدر ألاقي زر حجز الموعد" → not complaint. Documented in evaluation.md §6.
- **A3.1** K-Means k=4..10 on train complaints: silhouette 0.014–0.022, ARI ≤ 0.027, NMI ≤ 0.070. Weak structure, so H3 holds (`reports/clustering.md`).
- **A2.7** reports written: `evaluation.md`, `model_card.md`, `integration_notes.md`, `README.md`.

### Decisions
- Labels come from Claude subagents (user decision) and are reported as **AI-assisted reference labels**, not human gold (a deviation from spec §4 A1.7, to be recorded in `integration_notes.md`).
- G2 gate variant (adding AURA bug_report as training data) is **dropped**. AURA-Cls items stay out of training so that their human labels serve as a clean external check.

### Blockers
- A3.2 MARBERT: BLOCKED pending owner approval (spec: no transformer without approval).
- Human gold: none. Recommended human spot-check of ~100 test items (integration_notes.md).

### Next
P0 complete. Awaiting owner decision: (a) approve one MARBERT fine-tune (A3.2), (b) human spot-check, (c) more TRANS/UX data. Do not re-run evaluate.py as a new test (only as a reproduction check).
- Determinism verified (2026-10-30): retrain from scratch, then evaluate.py gave 'REPRODUCTION CHECK: identical metrics'. Only timestamps and training_time_s differ in the register and manifest. pytest 20 passed.

## 2026-10-30: A4 improvement phase (branch `agent/claude-ml-a4`)
- A4.1: tag `baseline-v1` = a02d2fa. Worktree `ml/.worktrees/a4/ml`; baseline artifacts copied to `artifacts/baseline-v1/` (sha256 in `reports/baseline_v1_artifact_sha256.txt`). The main `ml/` tree and `ml/artifacts` are unchanged; Codex imports from there. New venv (torch 2.15, transformers 5.22, cleanlab 2.9, sklearn 1.9.1).
- Considered and rejected `Ruqiya/Arabic_Reviews_of_SHEIN` (Apache-2.0): product-quality reviews, not digital-service failures.
- A4.2 cleanlab: 239/1,665 v1 train/val flagged. Inspection: most flags reflect model weakness (OOF 7-way macro-F1 0.465), not label errors, so no confidence-only relabeling.
- A4.3 holdout frozen (commit e3ccd24, ids sha 65fb9459): random 900 + enr_trans 150 + enr_ux 150 + enr_codeswitch 40. Code-switching is rare in AURA (126 of 17,380 pool reviews have any English word).
- A4.4 guide v1.1 frozen (commit 7341ed7). A4.5 Fable pilot κ 0.80 vs v1 final (Haiku 0.70), so B = fable.
- A4.6 holdout labels: A vs B complaint κ 0.873, joint κ 0.843, category κ 0.880; 124 adjudicated. Fable coders were auto-restarted after a usage-limit interruption; final files come from the completed rerun, and the adjudication ran afterwards.
- A4.7 re-review: blind agreed 200/239; 39 adjudicated; 32 labels changed (mostly AVAIL→OTHER 11, UX→OTHER 6).
- Selection protocol pre-registered (commit e541832).
- Code: `src/a4_common.py`, `src/hf_model.py` (MARBERT fine-tune + fp16 export, verified max |ΔP| 2e-4 vs fp32), `infer.py` multi-backend (default unchanged; 20/20 v1 tests pass, identical output), scripts a4_{split,experiments,select,evaluate}.
- Disk: about 11–12 GB free (other system activity); models are exported in fp16 (about 328 MB each).
- Labels: 4,000 a4_train (κ 0.871/0.839/0.879); synthetic 300/300 blind-verified (verifier read only guide + texts). Split sha 6719e22c: train 4,884 + 300 synthetic, val 815, holdout 1,240, v1_test 301.
- Val (A4): E1 tfidf 0.596 e2e / gate 0.874; E2 tfidf+synthetic **0.605** / 0.881 (synthetic retained, +0.009); E5 e5+LR 0.514. E0 baseline on val is contaminated (198/815 val items in v1 train), so it is compared only on the holdout.
- Owner asked to stop (2026-10-30): MARBERT grid stopped before its first epoch (no results). hf-7way backend smoke test via predict_text with a STUB untrained model: contract OK.
- **Open:** MARBERT grid + seeds, a4_select, holdout evaluation (holdout NOT yet evaluated), A4 reports.
- **A4 completed (2026-10-30/31).** MARBERT grid (lr {2e-5, 4e-5} × {ce, sqrt-weights}); best lr 4e-5 + sqrt weights. E3 seeds 42/13/7 val e2e 0.692/0.724/0.715 (mean 0.710). E4 (+synthetic) 0.720/0.711/0.731 (mean 0.720). MPS non-determinism: the same config/seed gave 0.6996 in the grid vs 0.6918 rerun.
- Selection (commit 2b15bc4, BEFORE holdout): E4_marbert_synth → `a4-marbert-v1` (median seed s42); +0.115 val e2e over E2 TF-IDF.
- **Holdout (once):** e2e 0.690 [0.634–0.736] vs baseline-v1 0.489 [0.437–0.536]; paired Δ +0.139…+0.260. Gate 0.913 vs 0.835. Category 0.729 vs 0.541. TRANS F1 0.78 vs 0.51; UX F1 0.76 vs 0.54. Code-switch subset (n=51) e2e 0.659 vs 0.428. Review rate 27% (auto accuracy 0.913) vs 40%. External AURA proxy κ 0.688 vs 0.604. Cost: 328 MB, 34 ms/msg CPU, 1.5 GB RSS.
- Honest note: E3 (no synthetic) scored slightly higher on the holdout (0.704 vs 0.690), within CI. The selection stays as pre-registered; no post-hoc switch.
- Reports regenerated (`reports/a4_report.md`, `a4_model_card.md`, `a4_annotation_provenance.md`, `a4_integration_notes.md`). Tests: 35 passed. The reproduction rerun of evaluate was skipped (to save tokens).
- Integration prep (2026-10-31): `SHA256SUMS` for the export, `requirements-a4-inference.txt` (pinned), extended `reports/a4_integration_notes.md` (promotion checklist, rollback, rebuild). Codex wrote `tests/test_a4_export_integrity.py` (12 passed: hashes, manifest, offline load, contract, consistency with HFPredictor, single load). Full suite: see the final commit message.

## 2026-10-31: P1 text + screenshot analysis (branch `agent/claude-ml-p1`)
- Worktree from A4 (aa4b394). Own venv (A4 pins + pillow, easyocr 1.7.2, pyobjc Vision 13.0). PaddleOCR is in `.venv-paddle` (it needs numpy 2.3.5). A4 model/v1 joblibs are hardlinked read-only from the A4 worktree.
- OCR (64 synthetic Chrome-rendered screens, 60 with text). CER/WER light: Vision **0.0021/0.016** (124 ms, 0.3 GB); EasyOCR-1600 0.034/0.151 (1.9 s, 6.3 GB); Paddle 0.048/0.125 (8.6 s, 12.6 GB); Tesseract 0.346/0.362. Default = Vision on macOS, EasyOCR elsewhere. No real screenshots available.
- Systems: registry v1 frozen before labelling. 339 AURA reviews (239 name-hit + 100 gov-app no-hit); coders sonnet/fable agree 334/339 (κ 0.982), 5 adjudicated (opus). Rules v1: P 0.958, R 0.628, F1 0.758; no-context ablation P 0.733 / R 0.945; substring P 0.511. 46/92 possible mentions are true. v1.1 aliases (in-sample) R 0.648.
- Pipeline with a4-marbert-v1 + Vision: OCR vs reference-text predictions 100% identical (60 images). Error screens 24/24 signal; narrative rule added after 6/36 user-text screens were false-flagged (dev). Real AURA check: 1.0% of reviews false-flagged (62.5% of the cue-containing ones). Per screenshot p50 136 ms; peak RSS 1.56 GB; warm-up 3.8 s.
- Known model behaviour: "a past, resolved problem" → complaint (needs_review). Reported, not patched.
- Tests: Codex wrote `tests/test_p1_{ocr,systems,analyze}.py` (108 tests). In Codex's sandbox, Vision requests failed (14 failures, `engine_error`). In a normal session the **full suite passes: 155**. This is documented as a deployment risk (fallback `ML_OCR_ENGINE=easyocr`). Fixtures were regenerated with registry v1.1 (scenario outcomes unchanged).
