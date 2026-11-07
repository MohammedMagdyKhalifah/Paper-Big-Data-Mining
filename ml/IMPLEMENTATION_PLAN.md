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
