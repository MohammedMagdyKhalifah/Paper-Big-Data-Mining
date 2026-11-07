# Master Project Summary

**Project:** *Beyond Sentiment: Mining Actionable Service Failures from Arabic Digital Service Complaints Using Machine Learning* (MSc research project).

**Audit date:** 2026-11-07.
* **Branch:** `agent/claude-docs` in the ML repository (`Project/ml/`), created from `agent/claude-ml-p1@af72c54`.
* **Location:** these files live in `Project/ml/.worktrees/docs/ml/docs/`, a sparse checkout.
* **Read-only audit:** nothing was trained, re-evaluated or modified.

This file is the entry point for a human reader or another AI agent. The five companion documents are:

| Document | Contents |
|---|---|
| `COMPLETE_PROJECT_HISTORY.md` | Repository/branch map, timeline with commits, every phase (planned / implemented / problems / status), proposal → implementation deviations, problems and lessons |
| `COMPLETE_ML_METHODOLOGY.md` | Datasets (sources, revisions, licences, composition, uniqueness), AI-assisted annotation, preprocessing, splits, models, training, evaluation protocol, **final model specification** |
| `ALL_EXPERIMENTAL_RESULTS.md` | Metric glossary and every recorded result: v1, preprocessing, classical, A4 validation, MARBERT grid, seeds, synthetic data, selection, holdout, per-class, errors, cost, clustering, agreement, P1 |
| `SYSTEM_IMPLEMENTATION_AND_P1.md` | P1 OCR / system identification, the full-stack application, API, feature-status table, integration status |
| `RESEARCH_FINDINGS_AND_LIMITATIONS.md` | RQ1–RQ5 / H1–H5 answers, objectives, negative findings, validity, unverified items, suggested report wording |

Earlier evidence documents that these files consolidate:
* `reports/ACADEMIC_ML_EVIDENCE.md` (ML, 2026-10-31).
* `integration/app/ACADEMIC_IMPLEMENTATION_EVIDENCE.md` (application, Codex, 2026-10-31).

---

## 1. What the project is

* **Task.** A local, offline Arabic NLP pipeline that works in two steps:
  1. A **gate** decides whether a short app-review text is a technical complaint.
  2. If it is, the text is assigned **one primary failure category**: AUTH, AVAIL, PERF, TRANS, UX or OTHER.
* **Web application.** It sits on top of the pipeline and stores, reviews and aggregates predictions.
* **P1 extension.** Adds screenshot OCR and registry-based Saudi government system-name identification.
* **Constraints.**
  * No cloud or API inference: trained models run locally.
  * Claude models served **only as annotators**.
  * Claude owns `ml/`; Codex owns `app/` and `integration/`.
  * The cross-stream contract `ml.infer.predict_text(text) -> {is_complaint, complaint_score, category, category_score, needs_review, model_version}` is frozen and unchanged across v1, A4 and P1.

## 2. Phase status (verified from Git and files)

| Phase | Branch @ commit | Status |
|---|---|---|
| Proposal and plans | `Project/*.docx`, `*_PLAN*.md` | Done |
| **P0-ML** (A0–A3): v1 TF-IDF baseline, K-Means | `agent/claude-ml` @ `7040c03` / `a02d2fa` (tag `baseline-v1`) | **COMPLETE** |
| P0-App: web app with the Mock model | `app/` `agent/codex-app` @ `e034f9b` | COMPLETE |
| Integration I: real v1 in the app | `integration/real-ml` @ `d835a86` | COMPLETE (browser-verified) |
| **A4**: data expansion + MARBERTv2, pre-registered, frozen holdout | `agent/claude-ml-a4` @ `aa4b394` | **COMPLETE** |
| A4 integration + standalone environment | `integration/a4-marbert` @ `01f0b43`; `integration/a4-environment` @ `3b2c2cf` | **COMPLETE**: latest fully verified integrated baseline |
| **P1-ML**: OCR + system identification | `agent/claude-ml-p1` @ `d8ffad4` | **COMPLETE** as an ML component (synthetic OCR evaluation only) |
| P1 integration | `integration/p1` @ `035f3eb` (docs `071716d`) | **PARTIAL**: API and component tests pass; browser and normal-host Vision acceptance **not done** |
| Documentation | `af72c54`; `071716d`; `agent/claude-docs` (this audit) | Done |

## 3. Data in one paragraph

**Sources.**
* AURA-Sentiment (29,700 rows) and AURA-Classification v2.0 (2,900 rows, human labels).
* Both are MIT-licensed, pinned on the Hugging Face Hub and undated.
* Of 32,600 raw records, 10 were excluded and the rest form 29,062 duplicate groups.

**Annotated real items: 7,240.** All of them are unique: 7,240 distinct records **and** 7,240 distinct duplicate groups, and no group spans splits (re-verified in this audit).
* Sources: 6,942 AURA-Sentiment and 298 AURA-Classification.
* Composition: v1 sample 2,000 + A4 expansion 4,000 + A4 holdout 1,240.
* Domain: **46.8% gov-domain**, from 45 gov apps. It is **multi-domain Arabic app reviews, not Saudi-e-government-only**.

**Synthetic items: 300.** LLM-generated and blind-verified; used for training only.

**A4 splits.** Train 4,884 + synthetic 300 / val 815 / holdout 1,240 / v1 test 301. The scored counts exclude UNCLEAR items: holdout 1,231, val 801, v1 test 295.

**Labels.** All labels are **AI-assisted**:
* v1: Sonnet + Haiku, with a Sonnet adjudicator.
* A4: Sonnet + Fable, with an Opus adjudicator.

**None are human gold.**

## 4. Most important confirmed results

| # | Result | Dataset | Source |
|---|---|---|---|
| 1 | v1 gate macro-F1 **0.845** [0.801, 0.884] vs Dummy 0.363; category **0.568** [0.454, 0.659] vs 0.078; e2e 0.553 | v1 test, n = 295 | `results/test_metrics.json` |
| 2 | **Selected `a4-marbert-v1` (E4)** e2e **0.690** [0.634, 0.736] vs v1 **0.489** [0.437, 0.536]; **paired Δ [+0.139, +0.260]**; gate 0.913 vs 0.835; category 0.729 vs 0.541 | A4 holdout, n = 1,231 | `results/a4/holdout_metrics.json` |
| 3 | TRANS F1 0.781 vs 0.506; UX 0.759 vs 0.535; PERF 0.522 vs 0.333 (n = 14) | A4 holdout | same |
| 4 | Selection by pre-registered validation rule: E4 0.7203 vs E3 0.7103 (3-seed means). E3 scored higher on the holdout (0.704), but there was no post-hoc switch | A4 val / holdout | `results/a4/selection.json`; commits `2b15bc4` → `1d3cbfa` |
| 5 | Cost: 34.3 ms vs 1.2 ms per message; 328 MB vs 3.3 MB; 1.53 GB RSS | CPU, M2 Max | `holdout_metrics.json: cost_selected_export` |
| 6 | Auto accuracy 0.913 at a 27% review rate (target 0.90); 0.895 on the enriched strata | A4 holdout | same |
| 7 | External human proxy (AURA bug_report) κ 0.604 → 0.688 | 2,604 AURA-Cls items | same |
| 8 | Inter-AI-coder κ: v1 complaint 0.781; A4 holdout complaint 0.873, joint 0.843 | annotation | `results/agreement.json`, `results/a4/agreement_a4.json` |
| 9 | K-Means: silhouette ≤ 0.022, NMI ≤ 0.070 (negative finding) | v1 train complaints | `results/kmeans.json` |
| 10 | OCR: Vision CER 0.0021 / WER 0.016, p50 124 ms; EasyOCR 0.034; Paddle 0.048; Tesseract 0.346 | **64 synthetic screenshots** | `results/p1/ocr_metrics_synthetic.json` |
| 11 | System identification (registry v1 rules): P 0.958, R 0.628, F1 0.758 | 339 AURA reviews, AI-assisted labels | `results/p1/mention_metrics_registry_v1.json` |
| 12 | Application: A4 browser, offline and rollback verified; 111 Python + 18 frontend tests (A4); 93 backend + 26 frontend tests (P1) | engineering | `integration/app/*VERIFICATION.md` |

**Re-verified in this audit:**
* A4 export `shasum -c SHA256SUMS`: 6/6 OK.
* v1 artifact hashes match.
* Per-run metrics.
* The 11 API routes exist in the source.
* Dataset uniqueness.

## 5. RQ / H verdicts

| | Verdict |
|---|---|
| RQ1 | TF-IDF is a useful but limited baseline: strong on AUTH/AVAIL, weak on TRANS/UX/OTHER |
| H1 | **Supported** |
| RQ2 / H2 | **Not tested as stated**: validation-only, small P1 gain; P2 not run |
| RQ3 / H3 | **Supported** (weak structure, imperfect correspondence) |
| RQ4 / H4 | **Supported** (large, significant gain at a modest cost; dialect recall not measured) |
| RQ5 / H5 | **Not evaluated** (no rubric, no sentiment benchmark) |

## 6. Missing evidence (do not claim)

1. Human gold labels or a human spot-check.
2. RQ5 actionability study.
3. P2 preprocessing; held-out normalisation test.
4. Per-domain, per-app or dialect metrics.
5. Dummy on the A4 holdout.
6. Paired tests other than E4 vs E0 (including E3 vs E4).
7. Per-class CIs; A4 calibration metrics.
8. Real-screenshot OCR accuracy; system detection on screenshots.
9. Full P1 browser acceptance; Vision on a normal host inside the app.
10. Peak MARBERT training memory; v1 RSS; recorded parameter count.
11. Licences of the pre-trained models.
12. The gov share of complaints.
13. A4 percent complaint agreement.
14. Any user study, expert evaluation or real-world deployment.

## 7. What remains unfinished

1. **P1 host acceptance.** Start the app on a normal macOS host, run all 155 ML tests with Vision, and run the real-browser P1 flows (OCR, edit, confirm, review, filters, restart, rollback). Commit the acceptance checkpoint (integration milestone M10).
2. **Real screenshots.** Put real screenshots in `data/ocr_eval/real/` with a manifest, then run `scripts/p1_ocr_run.py --set real` and `p1_ocr_eval.py --set real`. Only after that can any OCR accuracy claim for real screenshots be made.
3. **Human validation subset.** Recommended: about 100 test or holdout items labelled by a human.
4. **RQ5.** Design and apply the actionability rubric if it is to be claimed.
5. **Owner decision.** Whether to promote `a4-marbert-v1` as the default in `ml.infer`. The ML default is still `tfidf-baseline-v1`; the app selects A4 through `ML_ARTIFACT_DIR`.
6. **Optional analyses.** Dialect and per-app bias; leave-one-app-out; P2; per-class CIs.

## 8. Rules for any agent continuing this project

* **Ownership.**
  * Claude: `ml/` only.
  * Codex: `app/` and `integration/`.
  * Never edit the root plan files or the other stream's code.
  * Keep `predict_text` unchanged.
* **Holdout.** **Never re-run the A4 holdout or tune on it.** Never overwrite the v1 or A4 artifacts.
* **Reporting.**
  * Never call AI-assisted labels human gold.
  * Never pair v1-test numbers with A4-holdout numbers.
  * Never claim real-screenshot OCR accuracy from the synthetic set.
* **Recovery documents.** `IMPLEMENTATION_PLAN.md`, `PROGRESS.md` and `SESSION_HANDOFF.md` exist in each ML branch, and `integration/app/{IMPLEMENTATION_PLAN,PROGRESS,SESSION_HANDOFF}.md` on the integration side.
* **Environment quirk.** `git worktree add` on this disk can fail with `mmap failed: Operation timed out`. Use `git worktree add --no-checkout` with a sparse checkout for documentation-only work.
