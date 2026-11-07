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
