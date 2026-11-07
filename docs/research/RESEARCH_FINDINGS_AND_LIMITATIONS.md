# Research Findings and Limitations

**Project:** *Beyond Sentiment: Mining Actionable Service Failures from Arabic Digital Service Complaints Using Machine Learning*

**Document role:**
* Answer RQ1–RQ5 and H1–H5 of the proposal (`Project/481013386_MohammedKhalifah_5102_A1-X.docx` §1.2–1.3) from actual evidence.
* State the threats to validity and the negative or inconclusive findings.
* Suggest wording for the report's discussion.

The numbers come from `ALL_EXPERIMENTAL_RESULTS.md`, where each one cites its result file.

**Evidence tags.**
* **[F]**: a result file.
* **[R]**: a project record.
* **[I]**: interpretation.
* **NOT VERIFIED**: no evidence exists.

> **Ground rules for interpreting everything below.**
> * **Labels.** All reference labels are AI-assisted: Claude coders with a Claude adjudicator. Every "performance" figure is agreement with these labels, not with human gold.
> * **Datasets are not interchangeable.** v1-test numbers (n = 295) and A4-holdout numbers (n = 1,231) come from different datasets and are never paired.
> * **No user, expert or deployment evidence exists**: no user study, no expert evaluation, no real-world deployment and no real-screenshot evaluation.

---

## 1. Research questions and hypotheses

### RQ1: How effectively do TF-IDF-based classifiers distinguish actionable failure categories?

* **Experiments.**
  * v1 A2: 290-configuration validation grid, then a one-time test.
  * A4 E1/E2: TF-IDF re-tuned on A4 data, scored on the frozen holdout.
* **Evidence.**
  * v1 test: category macro-F1 **0.568** [0.454, 0.659]; gate 0.845.
  * v1 test per-class F1: AUTH 0.77, AVAIL 0.81, OTHER 0.53, UX 0.44, TRANS **0.18** (n = 8).
  * A4 holdout: category macro-F1 0.634 (E1) and 0.641 (E2); e2e 0.587 / 0.597. [F]
* **Interpretation [I].** TF-IDF is a useful but limited baseline. It is strong on lexically distinctive classes (AUTH: OTP, password; AVAIL: "لا يعمل"). It is weak on TRANS, UX and OTHER, whose expressions are more varied. Character n-grams beat word n-grams.
* **Limitations.**
  * The data is multi-domain: 46.8% of items are from gov apps. It is not Saudi-e-government-only.
  * The v1 test has very small TRANS, UX and PERF supports.
* **Unverified.** Per-domain (gov vs non-gov) breakdowns; leave-one-app-out generalisation.

### H1: At least one TF-IDF classifier will exceed the majority baseline on held-out macro-F1

* **Evidence (v1 test vs Dummy, 95% CI of the gain).** Gate **[+0.431, +0.528]**; category **[+0.374, +0.580]**. [F]
* **Verdict: SUPPORTED.** The lower CI bounds are far above zero.
* **Limitation.** Dummy was not evaluated on the A4 holdout. H1 rests on the v1 test, which is small: 295 items, 127 complaints.

### RQ2 / H2: Which normalisation decisions help? (H2: controlled normalisation improves held-out macro-F1; aggressive stemming may not)

* **Experiments.**
  * P0 vs P1 across 4 feature sets × LR/SVC, on v1 validation.
  * The A4 E1 grid, again with P0 and P1.
* **Evidence.**
  * The best P1 model exceeded the best P0 model by **+0.007** (gate) and **+0.024** (category), on **validation only** (125 complaints).
  * After re-tuning on A4 data, the selected gate used **P0** while the category model used P1. [F]
* **Verdict: NOT TESTED as stated.** The evidence is weak and mixed.
  * **No held-out comparison** of P0 vs P1 was run; only the selected variant was tested.
  * The aggressive variant **P2 (stemming / stop words) was never implemented.** The second half of H2 is therefore untested.
* **Interpretation [I].** Normalisation effects are small relative to the representation choice (character vs word n-grams) and to data size. MARBERT used P0 input with its own tokenizer.
* **Unverified.**
  * Per-variant minority-class recall on held-out data.
  * Confusion changes per variant.

### RQ3 / H3: Can K-Means expose interpretable themes? (H3: some coherent clusters, imperfect correspondence)

* **Experiment.** A3 K-Means on 586 v1 training complaints, with k = 4–10.
* **Evidence.**
  * Silhouette 0.014–0.022 and ARI ≤ 0.027 at every k. NMI was ≤ 0.070 overall and 0.0701 at the best k = 9.
  * Some coherent clusters exist: login/password (AUTH-dominant), "app not working" (AVAIL-dominant) and post-update problems. Most clusters are driven by style words (برنامج، جدا، للاسف، فاشل). [F]
* **Verdict: SUPPORTED**, in H3's own "imperfect correspondence" form. It is a **negative finding** for unsupervised discovery as a substitute for supervision.
* **Limitations.**
  * Only TF-IDF features were clustered; embeddings were not.
  * Clustering was not repeated on the larger A4 data.
  * No systematic manual coherence rating is recorded (NOT VERIFIED).

### RQ4 / H4: Does a fine-tuned Arabic transformer justify its cost? (H4: a dialect-aware transformer may improve recall on informal complaints, at measurable cost)

* **Experiment.** A4 E3/E4 (MARBERTv2, 10 runs) vs E0–E2 and E5, under the pre-registered protocol, with a single frozen-holdout evaluation.
* **Evidence** (A4 holdout, n = 1,231) [F]:

  | Measure | Selected E4 | Baseline v1 (E0) |
  |---|---|---|
  | E2E macro-F1 | **0.690** | 0.489 |
  | Paired Δ 95% CI (E4 − E0) | **[+0.139, +0.260]** | — |
  | Gate macro-F1 | 0.913 | 0.835 |
  | Category macro-F1 | 0.729 | 0.541 |
  | TRANS F1 | 0.781 | 0.506 |
  | UX F1 | 0.759 | 0.535 |
  | Code-switch gate (n = 51) | 0.919 | 0.852 |
  | External AURA κ | 0.688 | 0.604 |
  | Latency | 34.3 ms/msg | 1.2 ms/msg |
  | Size | 328 MB | 3.3 MB |
  | Peak RSS | 1.53 GB | — |
  | Training | ≈ 36 min for 10 runs, M2 Max MPS | — |

* **Decomposing the gain** [I, descriptive, no CI]:
  * Data effect (E1 − E0): +0.098.
  * Architecture effect (E4 − E2): +0.093.
  * Both contributed.
* **Verdict: SUPPORTED.** The gain is substantial and statistically clear, and the cost is measurable but modest on CPU.
* **Limitations.**
  * "Informal / dialect" recall could not be measured directly, because there are no dialect labels.
  * Peak training memory was not recorded.
  * The parameter count is derived (≈ 163 M), not recorded.
  * The gain is measured against AI-assisted labels.
* **Selection note.**
  * E3 (no synthetic data) scored higher on the holdout (0.704 vs 0.690).
  * E4 remains selected because the pre-registered, validation-only rule chose it (+0.0100 ≥ 0.005), and the selection was committed before the holdout was opened (`2b15bc4` → `1d3cbfa`).
  * The E3–E4 difference was not significance-tested.

### RQ5 / H5: How do category outputs compare with sentiment-only counts for diagnostic actionability?

* **Experiment: NONE.**
  * No predefined usefulness rubric was applied.
  * No expert or practitioner review took place.
  * No sentiment model was trained or benchmarked.
  * No category-vs-sentiment comparison was made.
  * AURA sentiment labels were deliberately hidden from coders and models.
* **Verdict: NOT EVALUATED.** The report may discuss RQ5 only conceptually, for instance by observing that the dashboard aggregates categories and systems rather than a negative-sentiment proportion, and should list it as future work.
* **Do not claim** that categories were shown to be more actionable than sentiment.

### Objectives (proposal §1.1)

| Objective | Status |
|---|---|
| O1: legally usable documented corpus, ≈ 1,200 complaints from ≥ 2 Saudi e-gov apps | **Met in volume (2,843 complaints), not in scope.** The data is licensed multi-domain AURA reviews (46.8% gov items; the gov share of complaints is NOT VERIFIED); there are no dates. Fully documented (`reports/data_manifest.md`). |
| O2: taxonomy, guide, 20% double-coding, κ | **Met with a deviation.** 100% double-coded by AI coders (κ reported); no human coders. |
| O3: Dummy / LR / SVM, reserved test, macro-F1, per-class recall, confusion; ablations | **Met**, apart from the held-out ablation and P2. |
| O4: K-Means + near-duplicate grouping | **Met** (negative clustering finding). |
| O5: errors, dialect/app bias, cost, value of categories; optional transformer | **Partial.** Errors, cost and the transformer were done. Dialect/app bias and category value (RQ5) were not. |

---

## 2. Additional findings (beyond RQ1–RQ5)

1. **Holdout discipline changed a conclusion.** On contaminated validation E0 > E1, but on the clean holdout E1 > E0. An independent holdout was necessary. [F/I]
2. **Synthetic augmentation is inconclusive.** It passed the validation rule for both architectures, but its holdout effect was +0.010 (TF-IDF) and −0.0145 (MARBERT). [F]
3. **Frozen multilingual embeddings (e5) underperformed TF-IDF** (holdout e2e 0.533 vs 0.587–0.597). [F]
4. **Abstention.**
   * The validation-chosen thresholds kept auto accuracy at 0.913 on the holdout (target 0.90), with 27% of items sent to review.
   * They missed the target on the enriched strata (0.895).
   * Only 36% of predicted complaints are decided automatically. [F]
5. **Errors concentrate where the AI coders were uncertain.** 79.8% of errors fall on such items, against a base rate of 34.2%, which points to reference ambiguity. [F/I]
6. **P1.**
   * On synthetic screens, OCR accuracy is high with Vision (CER 0.0021), and OCR noise did not change any classification.
   * Conservative system identification trades recall (0.63) for precision (0.96).
   * The error-screen signal is unreliable for texts that merely describe errors (62.5% false flags among them). [F]
7. **Engineering feasibility.** A fully local web application with the A4 model, persistence, review audit, offline loading and rollback was verified in a browser. The P1 browser workflow remains unverified. [R]

---

## 3. Negative and inconclusive findings (report these as findings)

1. K-Means does not recover the operational categories (NMI ≤ 0.07).
2. Synthetic augmentation brought no demonstrable holdout benefit for MARBERT.
3. Frozen e5 embeddings + LR were worse than TF-IDF.
4. Normalisation effects were small and validation-only, and the re-tuned A4 gate preferred P0.
5. Tesseract is unsuitable for UI screenshots (CER 0.346).
6. The error-screen rule produces many false flags on texts that mention errors.
7. MARBERT classifies resolved, historical problems as complaints.
8. Rules-based system detection misses about 37% of mentions.
9. v1 misclassified a common mixed-language OTP complaint; A4 fixed this case.
10. A noisy-OCR published screenshot of a services menu was classified as a complaint in the application probe.

---

## 4. Validity

### 4.1 Construct validity

* **Labels are not human gold.**
  * The only human anchor is AURA `bug_report`, a different construct that covers only the gate (κ 0.722 for the AI labels; 0.604 → 0.688 for the models).
  * The recommended human spot-check was **not done**.
* **Single model family.** All coders, adjudicators, the synthetic generator and the verifiers are Claude models. Errors may be correlated, and the high A4 κ (≈ 0.87 complaint, ≈ 0.84 joint) may partly reflect shared priors.
* **Symptoms, not causes.** Categories are stated symptoms, and "technical complaint" is defined operationally by the guide.
* **Systems are mentions, not attribution.** System identification records which systems are named; it does not attribute the failure to them.
* **Actionability (RQ5) is untested.**

### 4.2 Internal validity

* **Strengths.**
  * Cross-corpus duplicate grouping; group-aware splits.
  * A holdout frozen before labelling.
  * Pre-registered selection; commit-order evidence; enforced selection-before-evaluation.
  * Leakage tests.
  * Re-verified in this audit: 7,240 unique groups and no group spanning splits.
* **Residual threats.**
  1. E0 validation contamination.
  2. The v1 test is non-blind for A4.
  3. A single validation fold.
  4. Seed SD 0.010–0.017, and MPS non-determinism.
  5. The MARBERT grid winner chosen by a 0.0009 margin.
  6. Guide change v1.0 → v1.1.
  7. 32 labels changed after model-flagged re-review, which may bias labels toward model-learnable patterns.
  8. Thresholds tuned on validation missed the target on the enriched strata.

### 4.3 External validity

* **Population.**
  * Public, self-selected, short app-store reviews from many domains; about half the items come from gov apps.
  * There are **no dates**, so no temporal claims are possible.
  * Sampling deliberately over-represents negative sentiment (75% in the random stratum) and minority-class lexicons.
* **Untested inputs.**
  * E-mails, tickets, long or private complaints.
  * Dialect-specific performance.
  * **Real screenshots**: the OCR set is synthetic and macOS-rendered.
  * Non-government systems: the registry covers 30 gov services only.
* **Deployment.** Verified only for macOS arm64 with CPython 3.12.

### 4.4 Statistical conclusion validity

* **Small supports.** PERF (14 holdout / 6 v1-test items) and TRANS (8 v1-test items). No per-class CIs were computed.
* **Code-switch subset.** It has no UX items, which mechanically depresses its macro-F1.
* **Multiple comparisons.** Six candidates and four subsets, with no correction. Only E4 vs E0 is pre-registered and paired.

---

## 5. What remains unverified (consolidated)

1. Human gold labels or a human spot-check.
2. RQ5/H5 actionability.
3. P2 preprocessing; held-out P0 vs P1.
4. Per-domain, per-app and per-dialect metrics; leave-one-app-out.
5. Dummy on the A4 holdout; paired tests other than E4 vs E0; per-class CIs; A4 ECE/Brier.
6. Peak RSS of v1; peak MARBERT training memory; recorded parameter count.
7. The gov share of complaints.
8. A4 percent complaint agreement.
9. A systematic K-Means inspection record.
10. Real-screenshot OCR accuracy; system detection on screenshots and non-gov services.
11. The full P1 browser workflow; Vision on a normal host inside the app.
12. Licences of MARBERTv2, e5 and the OCR model weights (not recorded in the project files).
13. The documented reason why the v1 test is non-blind. The protocol states only the status; the interpretation is that it was already scored and its errors analysed in A2.

---

## 6. Recommended report discussion (suggested wording)

* **Labels.** "All reference labels were produced by independent large-language-model coders with model adjudication (AI-assisted reference labels). Reported metrics therefore measure agreement with these labels, not with human expert judgement. The only human anchor (AURA-Classification bug-report labels) supports the complaint gate (κ = 0.69 for the selected model)."
* **Main result.** "On a frozen holdout of 1,231 scorable items, evaluated once after a pre-registered selection, the fine-tuned MARBERTv2 model improved end-to-end macro-F1 from 0.489 to 0.690 over the TF-IDF baseline (paired bootstrap 95% CI of the difference: 0.139–0.260), at about 30× the CPU latency (34 ms vs 1.2 ms per message)."
* **Selection honesty.** "A variant without synthetic augmentation scored slightly higher on the holdout (0.704). The pre-registered validation-only rule was not overridden, and synthetic augmentation is therefore reported as inconclusive."
* **Scope.** "The corpus consists of licensed Arabic app reviews from multiple domains (about 47% government apps), without review dates. It is not a sample of Saudi e-government complaints in general."
* **P1.** "Screenshot OCR was benchmarked on synthetic, macOS-rendered screens only (Apple Vision CER 0.002). Real-world screenshot accuracy was not measured. The web extension integrating OCR and system identification passed API and component tests, but full browser acceptance remains outstanding."
* **Negative results.** Report K-Means, synthetic augmentation, e5 and Tesseract as findings, not as omissions.
* **Future work.**
  * A human-labelled validation subset.
  * An RQ5 actionability rubric with practitioners.
  * Dialect labels.
  * Real screenshots.
  * Per-app generalisation.
  * Multi-label classification.
