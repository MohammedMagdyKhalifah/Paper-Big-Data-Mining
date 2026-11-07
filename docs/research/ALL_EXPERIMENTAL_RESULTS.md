# All Experimental Results

**Project:** *Beyond Sentiment: Mining Actionable Service Failures from Arabic Digital Service Complaints Using Machine Learning*

**Document role:** this is the complete results record for every experiment that was actually run: the v1 baseline, A4 and P1. The methods are described in `COMPLETE_ML_METHODOLOGY.md`, interpretation is in `RESEARCH_FINDINGS_AND_LIMITATIONS.md`, and the overall index is `MASTER_PROJECT_SUMMARY.md`.

**Audit date:** 2026-11-07. Branch `agent/claude-docs`, created from `agent/claude-ml-p1@af72c54`. No model was trained, no evaluation was rerun and no data or weights were changed for this document.

## Conventions

* **Paths.** Paths are relative to the ML repository root (`Project/ml/`; the same tree as branch `agent/claude-ml-p1`) unless prefixed `integration/` (the integration repository `Project/integration/`).
* **Evidence tags.**
  * **[F]**: a value copied from the cited result file. These values were extracted on 2026-10-31 into `reports/ACADEMIC_ML_EVIDENCE.md`, and spot-checked against the source files on 2026-11-07. Nothing was recomputed.
  * **[V]**: re-verified in this audit by reading the file or running a read-only command on 2026-11-07.
  * **[R]**: reported in a progress or verification record of an execution that was not repeated in this audit.
  * **[D]**: derived by simple arithmetic from cited values.
  * **[I]**: interpretation.
* **Dataset discipline.**
  * Every table names its dataset and split.
  * Validation metrics (A4 validation, n = 801 scorable) and holdout metrics (A4 frozen holdout, n = 1,231 scorable) are **never mixed**.
  * v1-test metrics (n = 295 scorable) come from a different dataset and labelling regime, and are **never paired** with A4-holdout metrics.
* **Labels.** All reference labels are **AI-assisted reference labels**: independent Claude model coders with model adjudication. They are not human gold. "Accuracy" therefore always means agreement with these AI-assisted reference labels.

### Metric glossary (how to read every table)

| Metric | Exact meaning in this project |
|---|---|
| Precision (class c) | Of the items predicted as c, the fraction whose reference label is c. |
| Recall (class c) | Of the items whose reference label is c, the fraction predicted as c. |
| F1 (class c) | Harmonic mean of precision and recall for c (0 if both are 0; `zero_division=0`). |
| **Macro-F1** | The unweighted mean of per-class F1 over a fixed label list. Every class counts equally, regardless of size, so a rare class with low F1 (e.g. TRANS) pulls it down strongly. **It is not accuracy.** |
| Accuracy | The fraction of all items whose predicted label equals the reference label. It is dominated by large classes, especially NO. |
| Weighted-F1 | Per-class F1 weighted by support. Reported only for v1. |
| Gate macro-F1 | Macro-F1 over the two labels complaint / not complaint. |
| Category macro-F1 | Macro-F1 over the six categories (AUTH, AVAIL, PERF, TRANS, UX, OTHER), computed on **reference complaints only**: the category model's choice is scored whatever the gate predicted. |
| End-to-end (e2e) macro-F1 | Macro-F1 over 7 labels: NO plus the six categories. The prediction is NO if the gate says not-complaint; otherwise it is the predicted category. This is the primary A4 metric. |
| TRANS / UX recall (A4 tables) | Category-level recall among reference complaints (`src/a4_common.py: metrics`). |
| 95% CI | Percentile bootstrap: 2,000 resamples of evaluation items, seed 42. In v1 each test item is its own duplicate group. |
| Paired Δ CI | The bootstrap distribution of (model A − model B) computed on the same resampled items. |
| Review rate | The fraction of items with `needs_review = true`. |
| Auto coverage / auto accuracy | The fraction of items *not* flagged for review, and the e2e accuracy on those items. |
| Auto complaint coverage | The fraction of predicted complaints decided automatically (not flagged). |
| ECE / Brier | Expected calibration error / Brier score of predicted probabilities (v1 validation only). |
| Cohen's κ | Chance-corrected agreement between two coders. |
| CER / WER | Character / word error rate: edit distance ÷ reference length, micro-averaged over images. |
| Silhouette / ARI / NMI | Cluster cohesion (cosine) / adjusted Rand index / normalised mutual information against reference labels. |

---

## 1. V1 baseline experiments (branch `agent/claude-ml`, commit `7040c03`; tag `baseline-v1` = `a02d2fa`)

**Dataset.** v1 sample of 2,000 items, guide v1.0. Split: train 1,399 / val 300 / test 301 (`data/splits/split_info.json`, sha256 `451ab15d…`). Selection used **validation only**, and the test set was evaluated once. [F]

### 1.1 Grid and selected configuration (validation)

| Component | Experiment id | Configuration | Val macro-F1 | Source |
|---|---|---|---|---|
| Gate, Dummy (most frequent) | gate-000 | — | 0.365 | `results/experiment_register.csv` [F] |
| **Gate, selected** | gate-078 | P1, char_wb 2–5, min_df 1, LR C=10, class_weight balanced, sublinear TF | **0.875** | `artifacts/baseline-v1/manifest.json: selected` [F] |
| Category, Dummy | category-000 | — | 0.0793 | same [F] |
| **Category, selected** | category-160 | P1, char_wb 2–5, min_df 2, CalibratedClassifierCV(LR C=1, balanced, sigmoid, cv=5) | **0.6004** | same [F] |

* **Grid size.** 290 register rows: 96 gate configurations, 192 category configurations and 2 Dummies (`results/experiment_register.csv`). [F]
* **Review thresholds** (validation, target ≈ 0.90 automatic-decision precision): flag if 0.40 ≤ complaint_score < 0.60, or if category_score < 0.675. [F]
* **Calibration** (validation): gate Brier 0.0973, gate ECE 0.0736, category ECE 0.1367 (`artifacts/baseline-v1/manifest.json: calibration`). [F]
* **Dry-run calibration finding** (placeholder labels, not a result): uncalibrated LR (C=0.1, balanced) gave category ECE 0.60, and sigmoid calibration brought it to 0.11 (`PROGRESS.md`, 2026-10-29). [R]

### 1.2 One-time held-out test, v1 (n = 295 scorable = 301 − 6 UNCLEAR; `results/test_metrics.json`)

| Task | n | Macro-F1 (95% CI) | Dummy | Δ vs Dummy (95% CI) | Other |
|---|---|---|---|---|---|
| Gate | 295 | **0.8449** (0.8012–0.8836) | 0.3629 | (0.4307–0.5283) | complaint P/R/F1 0.815 / 0.835 / 0.825; auto-coverage 0.8915 at accuracy 0.8897 |
| Category | 127 | **0.5679** (0.454–0.6589) | 0.0783 | (0.3736–0.5801) | accuracy 0.6614; weighted-F1 0.6492; auto-coverage 0.1969 at accuracy 0.96 |
| End-to-end (7-way) | 295 | **0.5529** | — | — | accuracy 0.7356; review rate 0.3797; accuracy when not flagged 0.8962 |

All values in the table are [F].

* **Gate confusion** (reference × prediction; NO, complaint): [[144, 24], [21, 106]]. [F]
* **External human proxy.** AURA-Classification `bug_report` (human label) vs the v1 gate on 2,604 items from groups never used in training: agreement 0.836, κ 0.604. [F]
* **Reproduction.** A deterministic retrain gave "REPRODUCTION CHECK: identical metrics" (commit `a02d2fa`). [R]

---

## 2. Preprocessing comparisons (v1 validation only; n = 300 validation items, 125 complaints)

The table shows the best validation macro-F1 per cell (`results/experiment_register.csv`; reproduced in `reports/evaluation.md` §2). [F]

| Features | Gate P0 | Gate P1 | Category P0 (LR / SVC) | Category P1 (LR / SVC) |
|---|---|---|---|---|
| word 1-gram | 0.832 | 0.837 | 0.553 / 0.569 | 0.566 / 0.560 |
| word 1–2-gram | 0.834 | 0.834 | 0.509 / 0.534 | 0.543 / 0.545 |
| char_wb 2–5 | 0.868 | **0.875** | 0.576 / 0.552 | **0.600** / 0.580 |
| word 1–2 + char 2–5 | 0.871 | 0.864 | 0.584 / 0.552 | 0.587 / 0.575 |

* **Variants.**
  * P0 = minimal cleaning plus privacy masking.
  * P1 = P0 plus orthographic normalisation.
  * **P2 (stop words / light stemming) was never implemented or run.**
* **Best P1 − best P0.** Gate +0.007; category +0.024 [D]. These are validation-only differences. **No held-out P0 vs P1 test was performed.**
* **A4 re-tuning (E1 grid, A4 validation).** The selected gate used **P0** and the category model used **P1** (`results/a4/runs/E1_tfidf_a4/config.json`). [F]

---

## 3. Classical ML comparisons

| Learner | Where evaluated | Outcome |
|---|---|---|
| DummyClassifier (most frequent) | v1 val + v1 test | Gate 0.363, category 0.078 (test). Not run on the A4 holdout. [F] |
| TF-IDF + LogisticRegression | v1 grid (gate and category); A4 E1/E2 | Selected for the v1 gate and category, and for the E1 category. [F] |
| TF-IDF + LinearSVC (sigmoid-calibrated) | v1 grid (category); A4 E1/E2 | Not selected in v1. Selected for the **E2** category (word 1–2 + char 2–5, C=1, balanced). [F] |
| Word vs character vs combined n-grams | v1 grid; A4 grid | char_wb 2–5 best in v1. Combined word + char selected for the A4 E1/E2 category models (§2, §4). [F] |
| class_weight none vs balanced | v1 and A4 grids | balanced selected for every learned classical component. [F] |
| Frozen multilingual-e5-base embeddings + LR (E5) | A4 validation + holdout | Weakest learned model (val e2e 0.5144; holdout 0.5334). [F] |

---

## 4. A4 dataset-improvement experiments (A4 validation, n = 801 scorable = 815 − 14 UNCLEAR)

Source: `results/a4/selection.json: validation_table, families` and `results/a4/runs/*/metrics_val.json`. [F, V]

| ID | What changed | n_train | Val e2e | Gate | Category | TRANS recall | UX recall |
|---|---|---|---|---|---|---|---|
| E0_baseline_v1 † | frozen v1 artifact | 1,399 (v1) | 0.6446 | 0.8518 | 0.6654 | 0.5588 | 0.5135 |
| E1_tfidf_a4 | v1 architecture re-tuned on A4 data | 4,806 | 0.5961 | 0.8743 | 0.6757 | 0.6765 | 0.5135 |
| E2_tfidf_a4_synth | E1 grid + 300 synthetic | 5,106 | 0.6051 | 0.8809 | 0.6771 | 0.6765 | 0.5946 |
| E5_e5_lr | e5-base embeddings + LR (C=30, no class weight) | 4,806 | 0.5144 | 0.8558 | 0.5929 | 0.6176 | 0.5946 |
| E3_marbert_final | MARBERTv2, mean of 3 seeds (SD 0.0166) | 4,806 | 0.7103 | 0.9181 | 0.7572 | 0.7059 | 0.6487 |
| **E4_marbert_synth** | E3 + 300 synthetic, mean of 3 seeds (SD 0.0099) | 5,106 | **0.7203** | 0.9274 | 0.7617 | 0.6765 | 0.6216 |

† **E0's validation score is contaminated.** 198 of the 815 A4 validation items were v1 training items. This was re-verified in this audit: `data/a4/split_a4.csv` has 198 rows with `set = v1_train` and `a4_split = val` [V]. E0's validation score is therefore optimistic and was not used as evidence.

* **n_train.** 4,806 = 4,884 − 78 UNCLEAR training items [D]; 5,106 = 4,806 + 300 synthetic [D].
* **E2 deviation.** The protocol text calls E2 "E1 best config + synthetic". The code re-runs the small grid with synthetic data included, so E2's category learner (calibrated LinearSVC) differs from E1's (calibrated LR). This is a minor, disclosed deviation. [F]

---

## 5. MARBERTv2 hyperparameter grid (A4 validation, seed 42; `results/a4/runs/E3_marbert_lr*/metrics_val.json`)

| Run | lr | Loss | Val e2e | Gate | Category | e2e acc. | TRANS rec. | UX rec. | T | Best epoch | Train min | MPS driver mem at end (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E3_marbert_lr2e-05_ce_s42 | 2e-5 | CE | 0.5689 | 0.9190 | 0.5955 | 0.8227 | 0.7353 | 0.5946 | 1.25 | 6 | 3.99 | 2.56 |
| E3_marbert_lr2e-05_ce_sqrt_class_weights_s42 | 2e-5 | CE + sqrt weights | 0.6987 | 0.9212 | 0.7399 | 0.8390 | 0.7647 | 0.6486 | 1.00 | 3 | 3.22 | 3.64 |
| E3_marbert_lr4e-05_ce_s42 | 4e-5 | CE | 0.6811 | 0.9230 | 0.7235 | 0.8365 | 0.7059 | 0.6486 | 1.65 | 6 | 3.36 | 3.57 |
| **E3_marbert_lr4e-05_ce_sqrt_class_weights_s42** (chosen) | 4e-5 | CE + sqrt weights | **0.6996** | 0.9125 | 0.7483 | 0.8390 | 0.6471 | 0.7568 | 1.40 | 4 | 3.20 | 4.61 |

All values in this table are [V].

* **Margin.** The chosen configuration beat the runner-up by **0.0009** e2e, well inside seed noise. [D]
* **Class weighting** raised e2e by +0.130 (lr 2e-5) and +0.019 (lr 4e-5). [D]
* **The MPS memory field** (`mps_driver_mem_gb_end`) is the driver allocation at the end of training. It is not a peak measurement.

---

## 6. Three-seed stability experiments (A4 validation; `results/a4/runs/E{3,4}_*_s{13,42,7}/metrics_val.json`)

| Run | Val e2e | Gate | Category | e2e acc. | TRANS rec. | UX rec. | T | Best epoch | Train min |
|---|---|---|---|---|---|---|---|---|---|
| E3_marbert_final_s13 | 0.7238 | 0.9291 | 0.7829 | 0.8589 | 0.7647 | 0.6757 | 1.65 | 6 | 3.10 |
| E3_marbert_final_s42 | 0.6918 | 0.9140 | 0.7346 | 0.8352 | 0.6176 | 0.5676 | 1.20 | 3 | 4.02 |
| E3_marbert_final_s7 (median → E3 holdout candidate) | 0.7153 | 0.9113 | 0.7542 | 0.8340 | 0.7353 | 0.7027 | 1.20 | 3 | 2.70 |
| E4_marbert_synth_s13 | 0.7108 | 0.9347 | 0.7419 | 0.8539 | 0.6471 | 0.6216 | 1.70 | 6 | 3.26 |
| **E4_marbert_synth_s42** (median → exported `a4-marbert-v1`) | 0.7195 | 0.9223 | 0.7761 | 0.8539 | 0.7353 | 0.6486 | 1.65 | 5 | 5.88 |
| E4_marbert_synth_s7 | 0.7306 | 0.9253 | 0.7672 | 0.8552 | 0.6471 | 0.5946 | 1.75 | 6 | 3.21 |

All values in this table are [V].

* **Means and SDs.** E3 mean 0.7103 (SD 0.0166); E4 mean 0.7203 (SD 0.0099) (`selection.json: families`). [F]
* **MPS non-determinism.** `E3_marbert_final_s42` repeats the chosen grid configuration and seed, yet scored 0.6918 against 0.6996 in the grid run. The repeated run was not bit-identical (`PROGRESS.md`). [R]
* **Total MARBERT training time** over the 10 runs ≈ 35.9 min on MPS [D].

---

## 7. Synthetic augmentation comparisons

| Architecture | Without synthetic | With synthetic | Val Δ (rule: retain if ≥ 0.005) | Holdout Δ (descriptive only) |
|---|---|---|---|---|
| TF-IDF two-stage | E1 val 0.5961 / holdout 0.5868 | E2 val 0.6051 / holdout 0.5968 | +0.0090 → retained | +0.0100 [D] |
| MARBERTv2 | E3 val 0.7103 (mean) / holdout 0.7041 (s7) | E4 val 0.7203 (mean) / holdout 0.6896 (s42) | +0.0100 → retained | **−0.0145** [D] |

* **Synthetic set.** 300 items (syn_trans 90, syn_ux 70, syn_codeswitch 80, syn_hard_negative 60) generated by Claude Sonnet 5.5 and accepted 300/300 by a blind Claude Fable 5.1 verifier (`reports/a4_annotation_provenance.md`). [F]
* **Interpretation [I].** The holdout effect is inconclusive: positive for TF-IDF, negative for MARBERT, and both within plausible sampling and seed noise. No paired test was run for these contrasts.

---

## 8. Final model-selection decision (pre-registered; `configs/a4_selection_rule.yaml`, commit `e541832`)

**Decision log** (`results/a4/selection.json: decision_log`; decided 2026-10-30T11:44:39Z; `holdout_used: false`) [F]:
1. **Classical candidate: E2.** 0.6051 ≥ E1 0.5961 + 0.005, so synthetic data is retained.
2. **Transformer candidate: E4.** 0.7203 ≥ E3 0.7103 + 0.005, so synthetic data is retained.
3. **Best non-fine-tuned candidate: E2**, since E5 did not beat it.
4. **Replace?** The transformer gain is +0.1152 (≥ 0.02 required). The gate change was −0.0465, i.e. the gate *improved* (a drop of at most 0.01 is allowed), so the decision is **REPLACE**.
5. **SELECTED: E4_marbert_synth.** The median seed s42 is exported as **`a4-marbert-v1`**.

**Commit order (verified with `git log` in this audit)** [V]:
1. Holdout frozen: `e3ccd24` (2026-10-30 00:29).
2. Guide v1.1: `7341ed7` (00:30).
3. Protocol: `e541832` (08:48).
4. Selection: `2b15bc4` (14:44:49).
5. Holdout evaluation: `1d3cbfa` (14:48:19).

`scripts/a4_evaluate.py` refuses to run without a committed `results/a4/selection.json`. [F]

### Why E4 stays selected although E3 scored higher on the holdout

E3 (s7) scored 0.7041 holdout e2e, against 0.6896 for E4 (s42), a difference of +0.0145 [D]. Selection is fixed by the pre-registered rule, which uses only validation evidence; there E4's three-seed mean exceeded E3's by 0.0100 (≥ 0.005). Switching after seeing the holdout would turn the holdout into a tuning set and bias the final estimate. `PROGRESS.md` records: "no post-hoc switch" [R].

* **No significance test.** No E3-vs-E4 paired bootstrap exists, so significance is **NOT VERIFIED**. The difference is smaller than the half-width of E4's e2e CI (≈ 0.05) [D].
* **Gate.** On the holdout gate, E4 was higher (0.9125 vs 0.9024). [F]

### Validation-chosen review thresholds (`selection.json: candidates.*`) [F]

| Candidate (export run) | Gate review band | Category threshold | Val review rate | Val auto accuracy | Auto complaint coverage |
|---|---|---|---|---|---|
| E1 | [0.40, 0.60) | 0.675 | 0.3084 | 0.9007 | 0.3217 |
| E2 | [0.425, 0.575) | 0.775 | 0.3358 | 0.9211 | 0.2476 |
| E5 | [0.30, 0.70) | 0.775 | 0.3134 | 0.9018 | 0.3704 |
| E3 (s7) | empty (0.5 = 0.5) | 0.85 | 0.2060 | 0.9245 | 0.5299 |
| **E4 (s42)** | empty (0.5 = 0.5) | **0.90** | 0.2322 | 0.9171 | 0.3902 |

---

## 9. Frozen-holdout evaluation (A4 holdout; 1,240 frozen, **1,231 scored**; evaluated once in `1d3cbfa`)

Source: `results/a4/holdout_metrics.json`. All candidates were scored on the identical 1,231 items with their validation-chosen thresholds; E0 used its deployed thresholds. [F]

**Why 1,231, not 1,240.** Nine holdout items have the reference label UNCLEAR. The pre-registered metric excludes UNCLEAR (`configs/a4_selection_rule.yaml`), and `scripts/a4_evaluate.py` line 72 filters it.
* By stratum: random 6 (900 → 894), enr_trans 1, enr_ux 2, enr_codeswitch 0 (340 → 337) (`results/a4/agreement_a4.json: holdout.by_stratum`). [F]
* No item was dropped for any other reason.
* The same rule gives v1 test 301 → 295 and A4 validation 815 → 801.

### 9.1 Holdout_all (n = 1,231)

| Candidate | E2E macro-F1 | Gate macro-F1 | Category macro-F1 | E2E accuracy | TRANS recall | UX recall |
|---|---|---|---|---|---|---|
| E0_baseline_v1 | 0.4890 | 0.8349 | 0.5407 | 0.7116 | 0.4200 | 0.4359 |
| E1_tfidf_a4 | 0.5868 | 0.8806 | 0.6341 | 0.7717 | 0.6800 | 0.6282 |
| E2_tfidf_a4_synth | 0.5968 | 0.8830 | 0.6408 | 0.7742 | 0.6200 | 0.6410 |
| E3_marbert_final (s7) | 0.7041 | 0.9024 | 0.7559 | 0.8107 | 0.8600 | 0.8333 |
| **E4_marbert_synth (s42), selected** | **0.6896** | **0.9125** | **0.7290** | **0.8310** | **0.8200** | **0.7051** |
| E5_e5_lr | 0.5334 | 0.8369 | 0.5899 | 0.7344 | 0.5800 | 0.5897 |

### 9.2 Confidence intervals and paired deltas: E4 vs E0 (the only pre-registered inferential contrast; `ci95_holdout_all`) [F]

| Metric | E4 95% CI | E0 95% CI | Paired Δ (E4 − E0) 95% CI | Point Δ [D] |
|---|---|---|---|---|
| E2E macro-F1 | [0.634, 0.7359] | [0.4368, 0.5359] | **[0.1392, 0.2595]** | +0.2006 |
| Gate macro-F1 | [0.8959, 0.9283] | [0.8125, 0.8548] | **[0.0557, 0.0998]** | +0.0776 |
| Category macro-F1 | [0.6678, 0.78] | [0.4779, 0.5957] | **[0.1221, 0.2516]** | +0.1883 |

None of the three paired intervals includes zero.

### 9.3 Holdout subsets (descriptive; not population estimates except "random") [F]

| Candidate | Random (n = 894): e2e / gate / category | Enriched (n = 337): e2e / gate / category | Code-switch (n = 51): e2e / gate / category |
|---|---|---|---|
| E0 | 0.4777 / 0.8685 / 0.5130 | 0.4292 / 0.7470 / 0.4849 | 0.4275 / 0.8516 / 0.3837 |
| E1 | 0.5763 / 0.9034 / 0.6046 | 0.5548 / 0.8203 / 0.5971 | 0.5465 / 0.9364 / 0.5440 |
| E2 | 0.5682 / 0.8997 / 0.6043 | 0.5652 / 0.8392 / 0.6007 | 0.5418 / 0.8940 / 0.6095 |
| E3 | 0.6765 / 0.9161 / 0.7203 | 0.7057 / 0.8662 / 0.7521 | 0.6545 / 0.9190 / 0.6326 |
| **E4** | **0.6713 / 0.9230 / 0.7139** | **0.6459 / 0.8848 / 0.6708** | **0.6585 / 0.9190 / 0.6387** |
| E5 | 0.5110 / 0.8557 / 0.5175 | 0.5459 / 0.7871 / 0.6076 | 0.3855 / 0.8432 / 0.5393 |

* **Random stratum.** 75% negative sentiment by design, so it is not a natural prevalence sample.
* **Code-switch subset.** Defined as ≥ 1 Latin word of ≥ 2 letters, so it spans strata. It contains **no UX items**, which mechanically caps category macro-F1 at 5/6. PERF n = 1 and TRANS n = 3, so these values are indicative only.

### 9.4 External human proxy on the holdout model pair: AURA-Classification v2 `bug_report` (n = 2,604; `external_aura_proxy`) [F]

| Model | Agreement | κ | Precision vs bug_report | Recall vs bug_report |
|---|---|---|---|---|
| E0_baseline_v1 | 0.8356 | 0.6040 | 0.6539 | 0.7971 |
| E4_marbert_synth | 0.8706 | 0.6883 | 0.7081 | 0.8642 |

`bug_report` is a different construct from "technical complaint", and this check covers the gate only.

### 9.5 Secondary, NON-blind comparison on the v1 test (n = 295; `candidates.*.v1_test_NOT_BLIND`) [F]

| Candidate | E2E | Gate | Category | TRANS recall (n = 8) | UX recall (n = 11) |
|---|---|---|---|---|---|
| E0_baseline_v1 | 0.5529 | 0.8449 | 0.5679 | 0.125 | 0.3636 |
| E1_tfidf_a4 | 0.6386 | 0.8772 | 0.6335 | 0.125 | 0.4545 |
| E2_tfidf_a4_synth | 0.6143 | 0.8558 | 0.6535 | 0.125 | 0.5455 |
| E3_marbert_final | 0.7696 | 0.9069 | 0.8285 | 0.875 | 0.7273 |
| E4_marbert_synth | 0.6964 | 0.8952 | 0.7665 | 0.375 | 0.6364 |
| E5_e5_lr | 0.5845 | 0.8525 | 0.6260 | 0.500 | 0.5455 |

The protocol designates this table as non-blind and as no evidence for selection.
* **The same v1 model scores differently on the two datasets.** E0 scores 0.5529 on the v1 test but 0.4890 on the A4 holdout. The difference reflects the dataset, labelling regime and class mix, not a change in the model. **v1-test and A4-holdout numbers must never be presented as a paired comparison.**

---

## 10. Per-class results

### 10.1 v1 test (`results/test_metrics.json`) [F]

| Class | Category P | Category R | Category F1 | E2E F1 | Support |
|---|---|---|---|---|---|
| AUTH | 0.7857 | 0.7586 | 0.7719 | 0.7273 | 29 |
| AVAIL | 0.7857 | 0.8462 | 0.8148 | 0.7229 | 39 |
| OTHER | 0.5000 | 0.5588 | 0.5278 | 0.3889 | 34 |
| PERF | 0.5556 | 0.8333 | 0.6667 | 0.7143 | 6 |
| TRANS | 0.3333 | 0.1250 | 0.1818 | 0.1667 | 8 |
| UX | 0.5714 | 0.3636 | 0.4444 | 0.2857 | 11 |
| NO (gate) | 0.8727 | 0.8571 | 0.8649 | 0.8649 | 168 |

### 10.2 A4 holdout_all: category level (`candidates.<id>.holdout_all.per_class_category`) [F]

| Class | Support | E0 P / R / F1 | **E4 P / R / F1** | E3 F1 | E2 F1 | E1 F1 | E5 F1 |
|---|---|---|---|---|---|---|---|
| AUTH | 104 | 0.6532 / 0.7788 / 0.7105 | 0.8544 / 0.8462 / 0.8502 | 0.8444 | 0.7810 | 0.7873 | 0.6887 |
| AVAIL | 151 | 0.6400 / 0.7417 / 0.6871 | 0.7933 / 0.7881 / 0.7907 | 0.7603 | 0.6997 | 0.7224 | 0.7007 |
| PERF | 14 | 0.4000 / 0.2857 / 0.3333 | 0.6667 / 0.4286 / 0.5217 | 0.6667 | 0.5000 | 0.4211 | 0.3810 |
| TRANS | 50 | 0.6364 / 0.4200 / 0.5060 | 0.7455 / 0.8200 / 0.7810 | 0.7611 | 0.5905 | 0.6182 | 0.6105 |
| UX | 78 | 0.6939 / 0.4359 / 0.5354 | 0.8209 / 0.7051 / 0.7586 | 0.8333 | 0.6944 | 0.6853 | 0.6345 |
| OTHER | 120 | 0.4603 / 0.4833 / 0.4715 | 0.6391 / 0.7083 / 0.6719 | 0.6696 | 0.5794 | 0.5702 | 0.5243 |

### 10.3 A4 holdout_all: end-to-end (7-way) (`per_class_e2e`) [F]

| Class | Support | E0 P / R / F1 | **E4 P / R / F1** |
|---|---|---|---|
| NO | 714 | 0.8613 / 0.8613 / 0.8613 | 0.9271 / 0.9258 / 0.9264 |
| AUTH | 104 | 0.5891 / 0.7308 / 0.6524 | 0.8000 / 0.8462 / 0.8224 |
| AVAIL | 151 | 0.6118 / 0.6887 / 0.6480 | 0.7778 / 0.7881 / 0.7829 |
| PERF | 14 | 0.3750 / 0.2143 / 0.2727 | 0.7143 / 0.3571 / 0.4762 |
| TRANS | 50 | 0.3158 / 0.2400 / 0.2727 | 0.5556 / 0.6000 / 0.5769 |
| UX | 78 | 0.4694 / 0.2949 / 0.3622 | 0.7302 / 0.5897 / 0.6525 |
| OTHER | 120 | 0.3496 / 0.3583 / 0.3539 | 0.5649 / 0.6167 / 0.5896 |

* **No per-class confidence intervals were computed** (NOT VERIFIED).
* **PERF** (14 holdout items, 6 v1-test items) is too small for stable conclusions.

### 10.4 Holdout confusion matrices (rows = reference; columns = prediction; order NO, AUTH, AVAIL, PERF, TRANS, UX, OTHER) [F]

```
E4 (results/a4/confusion_holdout_E4_marbert_synth.csv)      E0 (results/a4/confusion_holdout_E0_baseline_v1.csv)
NO    661   7   3  0 14  9 20                                NO    615  15  15  0 17 13 39
AUTH    4  88   6  0  1  2  3                                AUTH    9  76   9  0  1  2  7
AVAIL   1   6 119  0  5  1 19                                AVAIL  14  13 104  0  4  1 15
PERF    3   2   2  5  0  0  2                                PERF    4   1   1  3  0  2  3
TRANS  14   1   2  0 30  1  2                                TRANS  19   7   4  0 12  3  5
UX     16   3   0  0  2 46 11                                UX     31   7   2  2  2 23 11
OTHER  14   3  21  2  2  4 74                                OTHER  22  10  35  3  2  5 43
```

---

## 11. Error analysis

### 11.1 v1 (test)

* **Category errors.** Listed in `results/errors_category_test.csv`, with the confusion matrix in `results/confusion_category_test.{csv,png}`. [F]
* **Probe misses** (`reports/evaluation.md` §6; `PROGRESS.md`) [R]:
  * The mixed-language "الـ OTP ما يوصلني when I try to login" was predicted not-complaint (complaint_score 0.32).
  * "ما أقدر ألاقي زر حجز الموعد" was also predicted not-complaint.
  * Integration testing later reproduced the first miss in the web application (0.3165) (`integration/app/PROGRESS.md`, checkpoint I2).

### 11.2 Selected A4 model (E4) on the holdout

These are descriptive counts from `results/a4/errors_holdout_selected.csv`: 208 errors = 1,231 − 1,023 correct. [F/D]

| Error type | Count |
|---|---|
| Gate false negatives (reference complaint → NO) | 52 |
| Gate false positives (reference NO → complaint) | 53 |
| Category confusions (complaint → wrong category) | 103 |

* **Main confusion pairs.** OTHER→AVAIL 21, NO→OTHER 20, AVAIL→OTHER 19, UX→NO 16, TRANS→NO 14, NO→TRANS 14, OTHER→NO 14.
* **Errors concentrate on hard items.**
  * 79.8% of errors are on items a coder flagged *uncertain*, against a base rate of 34.2%.
  * 29.8% are on *adjudicated* items, against a base rate of 10.0%.
  * This is consistent with reference-label ambiguity, not only model error [I].
* **TRANS gap.** E4's TRANS category recall is 0.82, but its end-to-end TRANS recall is 0.60. 14 of the 50 TRANS items were rejected by the gate.
* **Known qualitative failure** (P1 scenarios): a past, *resolved* problem ("كانت عندي مشكلة… انحلت") is classified as a complaint (AUTH, `needs_review`). This was reported, not patched (`results/p1/pipeline_eval.json: scenarios`). [F]
* **Application probe** (integration, Codex): a published Absher "services" screenshot, after noisy EasyOCR, was classified as a complaint. This is an undesirable qualitative observation, not a measured false-positive rate (`integration/app/P1_SCREENSHOT_OBSERVATIONS.json`). [R]

### 11.3 Review/abstention on the holdout (`candidates.<id>.<subset>.review`) [F]

| Candidate | Subset | Review rate | Auto coverage | Auto accuracy | Auto complaint coverage |
|---|---|---|---|---|---|
| E0 | all | 0.4029 | 0.5971 | 0.8844 | 0.2070 |
| **E4** | all | 0.2697 | 0.7303 | **0.9132** | 0.3591 |
| E4 | random | 0.2506 | 0.7494 | 0.9194 | 0.4027 |
| E4 | enriched | 0.3205 | 0.6795 | 0.8952 | 0.2448 |
| E3 | all | 0.2275 | 0.7725 | 0.9043 | 0.5286 |

E4's thresholds kept auto accuracy above the 0.90 target overall and on the random stratum, but not on the enriched strata (0.8952).

---

## 12. Computational performance

| Model / component | Size | Latency | Memory | Training | Source |
|---|---|---|---|---|---|
| tfidf-baseline-v1 | 3.3 MB (gate 1.03 MB + category 2.39 MB joblib) | ≈ 1.2 ms/message (mean over 200 test texts, CPU, M2 Max) | NOT VERIFIED | full 290-configuration grid ≈ 80–82 s CPU | `reports/evaluation.md` §3.4; `PROGRESS.md` [F/R] |
| a4-marbert-v1 (E4 s42) | 328.4 MB total; `model.safetensors` 325,716,998 bytes (fp16) | 34.31 ms/message via `predict_text`, serial, CPU (first call 3.07 s) | peak RSS 1,534.3 MB | 5.88 min (export run, MPS); 10 MARBERT runs ≈ 35.9 min [D] | `holdout_metrics.json: cost_selected_export` [F]; `integration/app/A4_MODEL_ASSETS.json` [R] |
| MARBERTv2 parameter count | ≈ 163 M [D: 325,716,998 B ÷ 2 B per fp16 parameter; header ignored] | — | — | — | not recorded in project files |
| E5 (e5-base + LR) | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | — |
| P1 pipeline (Vision + MARBERT) | — | p50 134.1 ms per screenshot (OCR 103.6, classify 31.8, systems 0.23) | peak RSS 1,555.6 MB | — | `results/p1/pipeline_eval.json` [F] |
| Web app, A4 (Codex probe) | — | median 37.0 ms per Analyze request including SQLite write (8 requests); cold start 4.99 s | peak RSS 1,535,344,640 B | — | `integration/app/A4_INTEGRATION_VERIFICATION.md` [R] |

* **Harness differences.** The latency figures come from different harnesses. Ratios such as "≈ 29× slower" are approximate [D/I].
* **Hardware.** M2 Max is recorded for the ML measurements. Exact chip and RAM were not recorded for the application probes.

---

## 13. Clustering (RQ3; v1 train complaints, n = 586; `results/kmeans.json`) [F]

| k | Silhouette (cosine) | ARI | NMI |
|---|---|---|---|
| 4 | 0.0143 | 0.0055 | 0.0283 |
| 5 | 0.0147 | 0.0146 | 0.0482 |
| 6 | 0.0151 | 0.0264 | 0.0517 |
| 7 | 0.0183 | 0.0026 | 0.0465 |
| 8 | 0.0196 | 0.0093 | 0.0511 |
| **9** | **0.0216** | 0.0271 | **0.0701** |
| 10 | 0.0187 | 0.0155 | 0.0614 |

* **Negative finding.** Structure is weak at every k, and correspondence with the operational labels is near zero.
* **Some coherent themes at k = 9.** AUTH-dominant login/password clusters, AVAIL-dominant "التطبيق لا يعمل" clusters, and a post-update cluster.
* **Not repeated on A4 data.**

---

## 14. Annotation agreement results

These are inter-AI-coder agreements, not human inter-annotator agreement.

| Set | n | Complaint % / κ | Joint (8-way) % / κ | Category κ | Adjudicated | Source |
|---|---|---|---|---|---|---|
| v1 pilot | 100 | 0.850 / 0.740 | 0.760 / 0.669 | 0.692 (n = 40) | — | `results/agreement.json: pilot` [F] |
| v1 overall | 2,000 | 0.8865 / 0.7810 | 0.8085 / 0.7130 | 0.7399 (n = 784) | 383 (19.1%) | `…: overall` [F] |
| A4 training expansion | 4,000 | NOT VERIFIED / 0.8706 | 0.9030 / 0.8392 | 0.8789 | 388 | `results/a4/agreement_a4.json: a4_train` [F] |
| A4 holdout | 1,240 | NOT VERIFIED / 0.8727 | 0.9000 / 0.8429 | 0.8804 | 124 | `…: holdout` [F] |
| P1 system mentions | 339 | item agreement 334/339; pair-level κ 0.9821 | — | — | 5 | `results/p1/mention_metrics_registry_v1.json` [F] |

**Further checks** [F]:
* **AI vs AURA human `bug_report`** (v1 overlap, n = 293): agreement 0.884, κ 0.722.
* **Blind Opus audit** (v1): audit = final on 0.800 of 120 disagreements and on 0.950 of 60 agreed items.

---

## 15. P1 results (summary; full detail in `SYSTEM_IMPLEMENTATION_AND_P1.md`)

### 15.1 OCR on 64 **synthetic** screenshots (60 with text; `results/p1/ocr_metrics_synthetic.json`) [F]

| Engine | CER light | WER light | CER clean / degraded | p50 latency | Peak RSS |
|---|---|---|---|---|---|
| Apple Vision (macOS 27.0.1) | **0.0021** | **0.0163** | 0.0012 / 0.0031 | 124.2 ms | 321 MB |
| EasyOCR 1.7.2 (canvas 1600) | 0.0338 | 0.1508 | 0.0258 / 0.0418 | 1,864.7 ms | 6,348 MB |
| EasyOCR 1.7.2 (canvas 2560) | 0.0351 | 0.1508 | 0.0285 / 0.0418 | 3,315.2 ms | 8,099 MB |
| PaddleOCR 3.7.0 (PP-OCRv5 arabic) | 0.0482 | 0.1247 | 0.0539 / 0.0425 | 8,614.8 ms | 12,607 MB |
| Tesseract 5.5.2 (tessdata_best ara+eng) | 0.3458 | 0.3623 | 0.3251 / 0.3665 | 276.9 ms | 192 MB (+159 MB child) |

### 15.2 System-name identification (339 AURA reviews, AI-assisted labels; 145 reference pairs) [F]

| Method | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| **Rules, registry v1 (frozen, shipped)** | 91 | 4 | 54 | **0.9579** | 0.6276 | 0.7583 |
| Ablation: ambiguous names without context | 137 | 50 | 8 | 0.7326 | 0.9448 | 0.8253 |
| Naive substring | 144 | 138 | 1 | 0.5106 | 0.9931 | 0.6745 |
| Rules, registry v1.1 (**in-sample, optimistic**) | 94 | 4 | 51 | 0.9592 | 0.6483 | 0.7737 |

### 15.3 Pipeline consistency and the error-screen rule [F]

* **OCR vs reference text.** Predictions from OCR text equal the predictions from the reference text in 100% of 60 synthetic images.
* **Error-screen rule on 2,000 real AURA reviews.** False-flag rate 0.010 overall, but 0.625 among the 32 reviews that contain an error cue.

---

## 16. Results that do NOT exist (do not report them)

1. Dummy baseline on the A4 holdout.
2. Paired tests other than E4 vs E0, including E3 vs E4 and E2 vs E1.
3. Per-class CIs.
4. A4 ECE/Brier.
5. Held-out P0 vs P1; P2 at all.
6. Per-domain, per-app or per-dialect metrics, and leave-one-app-out.
7. Human-gold evaluation.
8. Real-screenshot OCR accuracy.
9. A sentiment baseline or actionability rubric (RQ5).
10. E5 cost.
11. Peak RSS of v1; peak MARBERT training memory.
12. Percent complaint agreement for the A4 sets.
