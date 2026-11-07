# ML Implementation Plan — `ml/` (Claude Code)

Specification: `../CLAUDE_CODE_ML_RESEARCH_PLAN.md` (binding), proposal `../481013386_MohammedKhalifah_5102_A1-X.docx`.
Scope: research and ML inside `ml/` only. Never edit `app/`, the root README, or the root .gitignore. The contract `ml.infer.predict_text` is frozen (spec §3).
Status values: TODO / IN_PROGRESS / DONE / BLOCKED. A task is DONE only when its acceptance criteria have been verified.

## Phase A0: Skeleton & contract (P0)

| ID | Task | Pri | Deps | Deliverables | Acceptance | Verify | Status |
|---|---|---|---|---|---|---|---|
| A0.1 | Folder skeleton, git repo in `ml/` (branch `agent/claude-ml`), venv, pinned requirements | P0 | – | `ml/{configs,data,scripts,src,tests,reports,artifacts}`, `requirements.txt`, `.gitignore` | venv imports sklearn; branch exists | `git branch --show-current`; `.venv/bin/python -c "import sklearn"` | DONE |
| A0.2 | `infer.py` contract: lazy single load, ValueError on empty, explicit error on missing artifacts, no mock | P0 | A0.1 | `ml/__init__.py`, `ml/infer.py` | Contract tests pass | `cd ml && .venv/bin/pytest tests/test_contract.py` | DONE |
| A0.3 | Contract tests (stub marked STUB, plus real-artifact tests skipped until A2) | P0 | A0.2 | `tests/test_contract.py`, `tests/conftest.py` | Stub tests pass; real tests skip with reason | pytest | DONE |
| A0.4 | `ml/README.md` with run/test commands | P0 | A0.2 | README | Commands run from repo root | manual run | DONE |

## Phase A1: Data, annotation, splits (P0)

| ID | Task | Pri | Deps | Deliverables | Acceptance | Verify | Status |
|---|---|---|---|---|---|---|---|
| A1.1 | Download AURA-Sentiment + AURA-Classification v2 at pinned HF revisions, with sha256 provenance | P0 | A0.1 | `scripts/download_data.py`, `data/raw/*`, `data/raw/provenance.json` | 29,700 + 2,900 rows; license MIT verified on the cards | rerun script; check provenance | DONE |
| A1.2 | Text processing: PII masking, P0/P1 normalization, negation kept, exclusion rules | P0 | A0.1 | `src/text.py`, `tests/test_text.py` | tests pass | pytest | DONE |
| A1.3 | Exact + near-duplicate groups across both datasets | P0 | A1.2 | `src/dedup.py`, `data/interim/corpus.parquet`, `near_duplicate_pairs.json` | Every record has `dup_group`; spot-check of pairs near the 0.85 threshold | manual spot-check (done: formulaic near-dups, conservative) | DONE |
| A1.4 | App→domain mapping (games excluded from core) | P0 | A1.1 | `configs/app_domains.yaml` | All gov aliases mapped | prepare_data domain counts | DONE |
| A1.5 | Annotation sample (2,000 = 1,000 gov + 700 non-gov + 300 AURA-Cls external), batches with id+text only | P0 | A1.3, A1.4 | `scripts/prepare_data.py`, `data/annotation/sample.parquet`, `batches/*.jsonl`, `reports/record_flow.json` | 1 item per dup_group; pilot 100 + 4 main batches | assert in script; record_flow | DONE |
| A1.6 | Annotation guide | P0 | – | `reports/annotation_guide.md` | Covers 6 classes, complaint/not, negation, multi-issue, precedence | review | DONE (v1.0 frozen) |
| A1.7 | Pilot: coder A (sonnet) + coder B (haiku) on 100 items; review disagreements; freeze guide v1.0 | P0 | A1.5, A1.6 | `data/annotation/out/coder{A,B}_pilot.jsonl`, guide changelog | Outputs valid and complete; κ reported; guide frozen | `src/agreement.py` | DONE |
| A1.8 | Main labeling: A and B independently on 1,900 items; adjudicator (sonnet) on disagreements | P0 | A1.7 | `out/coder{A,B}_main_XX.jsonl`, `out/adjudication*.jsonl` | 100% coverage, valid schema | agreement script coverage check | DONE |
| A1.9 | Merge labels + agreement report (inter-AI κ, AI vs AURA human `bug_report`) | P0 | A1.8 | `scripts/build_labels.py`, `data/annotation/labels.parquet`, `reports/agreement.md` | label_a/b/final stored separately; deviation documented | rerun script | DONE |
| A1.10 | Group-aware stratified 70/15/15 split (seed 42) + sha256 | P0 | A1.9 | `src/split.py`, `data/splits/split_manifest.csv` | No group crosses splits; class counts reported | `tests/test_leakage.py` | DONE |
| A1.11 | Data manifest report | P0 | A1.1–A1.10 | `reports/data_manifest.md` | Source, license, date, columns, counts, limits, citation | review | DONE |

## Phase A2: Baselines, model export, evaluation (P0)

| ID | Task | Pri | Deps | Deliverables | Acceptance | Verify | Status |
|---|---|---|---|---|---|---|---|
| A2.1 | Complaint gate: Dummy vs TF-IDF+LR (word / char_wb), P0 vs P1, tuned on validation | P0 | A1.10 | `src/train.py`, `configs/experiments.yaml`, `results/experiment_register.csv` | Selection uses validation only | register rows reproducible | DONE |
| A2.2 | Category: Dummy, LR, LinearSVC (calibrated), word vs char, P0 vs P1, small grid | P0 | A1.10 | same | Selection by validation macro-F1 with rare-class recall in view | register | DONE |
| A2.3 | Thresholds for `needs_review` (≈0.90 precision on auto decisions, chosen on validation), plus calibration check (Brier/ECE) | P0 | A2.1, A2.2 | `artifacts/manifest.json` thresholds | Documented meaning | evaluation.md | DONE |
| A2.4 | Export artifacts; `infer.py` serves the real model | P0 | A2.1–A2.3 | `artifacts/{gate,category}.joblib`, `manifest.json` | Real contract tests pass | pytest (real tests no longer skipped) | DONE |
| A2.5 | One-time test evaluation: macro-F1, per-class P/R/F1 + support, confusion matrix, bootstrap CI, end-to-end, AURA external gate check, latency | P0 | A2.4 | `scripts/evaluate.py`, `results/*`, `reports/evaluation.md` | Numbers recomputable with one command | rerun evaluate.py → identical | DONE |
| A2.6 | Leakage tests | P0 | A1.10 | `tests/test_leakage.py` | Pass | pytest | DONE |
| A2.7 | Reports: model_card, integration_notes (contract unchanged, annotation deviation), README | P0 | A2.5 | `reports/model_card.md`, `reports/integration_notes.md`, `README.md` | Root integration command works | `PYTHONPATH=. ml/.venv/bin/python -c 'from ml.infer import predict_text; ...'` | DONE |

## Phase A3: One bounded improvement (conditional, only after A2)

| ID | Task | Pri | Deps | Deliverables | Acceptance | Verify | Status |
|---|---|---|---|---|---|---|---|
| A3.1 | Small K-Means comparison (proposal RQ3): k∈4–10, silhouette, ARI/NMI, top terms | P1 | A2.5 | `scripts/kmeans.py`, `reports/clustering.md` | Documented, no alerting system | rerun | DONE |
| A3.2 | MARBERT fine-tune (MPS), **only with user approval** | P2 | A2.5 | – | – | – | BLOCKED (needs approval) |

Deferred (do not start): LoRA, 14B teacher, NER, OCR/EML/system extraction (Codex).

## Phase A4: Evidence-driven improvement (authorised by the owner 2026-10-30). Branch `agent/claude-ml-a4`, worktree `ml/.worktrees/a4/ml`

Rules: v1 (`tag baseline-v1`, `ml/artifacts`) stays untouched for Codex. The new holdout is frozen before training, and selection is pre-registered (`configs/a4_selection_rule.yaml`). The holdout is evaluated once after `results/a4/selection.json` is committed. All labels are AI-assisted, not human gold.

| ID | Task | Pri | Deps | Deliverables | Acceptance | Verify | Status |
|---|---|---|---|---|---|---|---|
| A4.1 | Preserve baseline: tag, worktree, artifact snapshot + sha256 | P0 | – | tag `baseline-v1`, `artifacts/baseline-v1/`, `reports/baseline_v1_artifact_sha256.txt` | main tree unchanged; Codex import unaffected | `git worktree list`; sha file | DONE |
| A4.2 | cleanlab confident-learning scan of v1 train/val (5-fold OOF) | P0 | A4.1 | `scripts/a4_label_issues.py`, `data/a4/label_issues_v1.csv` | flagged set produced; no automatic relabel | summary json | DONE (239 flagged) |
| A4.3 | Freeze new holdout (1,240: 900 representative + 340 enriched) + draw 4,000 training expansion | P0 | A4.1 | `scripts/a4_prepare.py`, `data/a4/holdout_sample.parquet` (ids sha 65fb9459) | disjoint dup groups; committed before labeling | assert + commit e3ccd24 | DONE |
| A4.4 | Guide v1.1 (clarifications only) frozen before A4 labeling | P0 | A4.2 | `reports/annotation_guide.md` | definitions unchanged; commit before labeling | commit 7341ed7 | DONE |
| A4.5 | Coder check: Fable on pilot (κ 0.80 vs v1 final; Haiku 0.70) | P1 | – | `data/a4/coder_check/` | chosen B = fable | agreement calc | DONE |
| A4.6 | Holdout labeling (sonnet + fable, opus adjudicator on anonymised shuffled disagreements) | P0 | A4.3–A4.5 | `data/a4/out/*holdout*` | 100% coverage, valid | `a4_build_labels.py` | DONE |
| A4.7 | Re-review of 239 flagged v1 labels (blind fable → opus adjudication with reason) | P0 | A4.2 | `data/a4/out/*rereview*` | provenance + reasons stored | build_labels stats | DONE (32 changed) |
| A4.8 | Training-expansion labeling (16 × 250) + synthetic (300 generated, blind-verified) | P0 | A4.3 | `data/a4/out/*train*`, `data/a4/batches/synthetic_00.jsonl` | 100% coverage; synthetic verified | build_labels | DONE |
| A4.9 | Merge with provenance + A4 split (train/val/holdout/v1_test/synthetic) | P0 | A4.6–A4.8 | `data/a4/labels_a4.parquet`, `data/a4/split_a4.csv` | leakage asserts; tests | `tests/test_a4.py` | DONE |
| A4.10 | Experiments E0–E5 on train/val | P0 | A4.9 | `results/a4/runs/*` | per protocol | metrics_val.json per run | DONE |
| A4.11 | Selection + export (`artifacts/a4/export/<version>`) committed before holdout | P0 | A4.10 | `results/a4/selection.json` | rule applied mechanically | commit | DONE |
| A4.12 | One-time holdout evaluation + reproduction check | P0 | A4.11 | `results/a4/holdout_metrics.json` | CIs, per-class, review, cost | rerun → identical | DONE |
| A4.13 | Reports: A4 report, provenance, model card, integration notes, docs; tests; commit | P0 | A4.12 | `reports/a4_*.md` | all tests pass | pytest | DONE |

## Phase P1: Arabic text + screenshot analysis (owner brief 2026-10-31). Branch `agent/claude-ml-p1`, worktree `ml/.worktrees/p1/ml` (from A4)
Rules: no MARBERT retraining or A4 holdout evaluation; `predict_text` unchanged; A4 artifacts read-only (hardlinked, never written); local/offline only; no email/EML.
- P1.1 OCR `src/ocr.py`: engines vision/easyocr/tesseract/paddle; status ok/empty/failed; synthetic eval set `data/ocr_eval/synthetic` (+ `real/` slot); CER/WER `src/ocr_metrics.py`, `scripts/p1_ocr_{run,eval}.py`. **DONE**: default Vision (macOS), EasyOCR elsewhere.
- P1.2 systems `src/systems.py` + `configs/systems.yaml`: rules + registry, conservative (ambiguous names need context). Registry v1 frozen (a3035f4) before labels; AI-assisted blind mention labels (339 items); `scripts/p1_mention_{sample,eval}.py`. **DONE** (v1.1 aliases = in-sample).
- P1.3 `analyze.py`: `analyze()`, `warmup()`, schema p1-analysis-v1, error-screen signal (configs/error_cues.yaml). **DONE**.
- P1.4 `scripts/p1_pipeline_eval.py` (consistency, kinds, scenarios, cost, real-text error-flag check); fixtures `tests/fixtures/p1/`; tests (Codex) `tests/test_p1_*.py`. Reports `reports/p1_report.md`, `p1_integration_notes.md`, `p1_mention_guide.md`.
