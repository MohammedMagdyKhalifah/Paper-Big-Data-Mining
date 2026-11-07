# Evaluation Report — `tfidf-baseline-v1`

All numbers come from `results/test_metrics.json` (`scripts/evaluate.py`, run once on 2026-10-29 after model selection was frozen; a second run printed `REPRODUCTION CHECK: identical metrics`). Validation numbers come from `results/experiment_register.csv` (`scripts/train.py`).
Split manifest sha256 `451ab15d…a6dff4fd`, seed 42. Bootstrap: 2,000 resamples of test items (each item is its own duplicate group).

**Read first:** reference labels are **AI-assisted** (two independent Claude coders + adjudicator; `agreement.md`), not independent human gold. Scores measure agreement with those reference labels. The one human anchor is the AURA-Classification proxy (§5).

## 1. Data used
| split | items | technical complaints | not complaint | unclear |
|---|---|---|---|---|
| train | 1,399 | 586 | 785 | 28 |
| val | 300 | 125 | 169 | 6 |
| test | 301 | 127 | 168 | 6 |

Test complaints by category: AUTH 29 · AVAIL 39 · OTHER 34 · PERF **6** · TRANS **8** · UX 11. PERF and TRANS test counts are too small for stable per-class conclusions.
`unclear` items are excluded from the gate and from end-to-end scoring.

## 2. Model selection (validation only)
Grid: preprocessing {P0, P1} × features {word 1-gram, word 1–2-gram, char_wb 2–5-gram, word+char} × min_df {1, 2} × C {0.1, 1, 10} × class_weight {none, balanced}. Gate learner: LR. Category learners: sigmoid-calibrated LR, sigmoid-calibrated LinearSVC. 96 gate and 192 category configurations, plus Dummy.

Best validation macro-F1 per variant/feature (max over the other hyper-parameters):

| features | gate P0 | gate P1 | category P0 (LR / SVC) | category P1 (LR / SVC) |
|---|---|---|---|---|
| word 1-gram | 0.832 | 0.837 | 0.553 / 0.569 | 0.566 / 0.560 |
| word 1–2-gram | 0.834 | 0.834 | 0.509 / 0.534 | 0.543 / 0.545 |
| char_wb 2–5 | 0.868 | **0.875** | 0.576 / 0.552 | **0.600** / 0.580 |
| word + char | 0.871 | 0.864 | 0.584 / 0.552 | 0.587 / 0.575 |

- **Selected gate:** P1 + char_wb(2–5), min_df 1, LR C=10, balanced (val macro-F1 0.875; Dummy 0.365).
- **Selected category model:** P1 + char_wb(2–5), min_df 2, calibrated LR C=1, balanced (val macro-F1 0.600; Dummy 0.079).
- RQ2 (exploratory): character n-grams beat word n-grams in both tasks, and P1 normalisation is slightly better than P0 for the best configurations (+0.007 gate, +0.024 category). The validation set is small (125 complaints), so the deltas are indicative only. P2 (stemming/stop-words) was not run.

## 3. Held-out test results
### 3.1 Complaint gate (n=295)
| metric | value |
|---|---|
| **macro-F1** | **0.845** (95% CI 0.801–0.884) |
| Dummy (most frequent) macro-F1 | 0.363 |
| Δ vs Dummy | +0.482 (CI 0.431–0.528) |
| not-complaint P / R / F1 (n=168) | 0.873 / 0.857 / 0.865 |
| complaint P / R / F1 (n=127) | 0.815 / 0.835 / 0.825 |
| confusion (ref × pred) | not: 144 ✓ / 24 ✗ · complaint: 21 ✗ / 106 ✓ |
| auto-decided share (outside review band [0.40, 0.60)) | 89.2%, with accuracy 0.890 on those |

### 3.2 Category classifier (reference complaints, n=127)
| metric | value |
|---|---|
| **macro-F1** | **0.568** (95% CI 0.454–0.659) |
| Dummy macro-F1 | 0.078 |
| Δ vs Dummy | +0.490 (CI 0.374–0.580) |
| accuracy / weighted-F1 | 0.661 / 0.649 |
| auto-decided share (category_score ≥ 0.675) | 19.7%, with accuracy 0.960 on those |

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| AUTH | 0.786 | 0.759 | 0.772 | 29 |
| AVAIL | 0.786 | 0.846 | 0.815 | 39 |
| OTHER | 0.500 | 0.559 | 0.528 | 34 |
| PERF | 0.556 | 0.833 | 0.667 | 6 |
| TRANS | 0.333 | 0.125 | 0.182 | 8 |
| UX | 0.571 | 0.364 | 0.444 | 11 |

Confusion matrix: `results/confusion_category_test.{csv,png}`. Errors: `results/errors_category_test.csv` (43 items).

### 3.3 End-to-end (gate → category vs reference joint label, n=295)
macro-F1 over {6 categories + NO} **0.553**, accuracy 0.736. `needs_review` flags 38.0% of messages, and accuracy on the unflagged 62% is **0.896**.

### 3.4 Cost
Inference is about **1.2 ms per message** on CPU (M2 Max, mean over 200 test texts). The full training grid takes about 80 s on CPU.

## 4. Hypothesis check
- **H1 (beats Dummy):** supported for both tasks on held-out test. The category macro-F1 gain (+0.49, CI lower bound 0.37) far exceeds the provisional +0.10 criterion.
- **H2 (normalisation helps):** weakly supported on validation only (P1 ≥ P0 for the best configurations). Untested on test by design, and P2 was not run.
- **H3 (K-Means themes):** see `clustering.md`. Weak structure (silhouette ≈ 0.02, NMI ≤ 0.07), so H3's "imperfect correspondence" holds.
- **H4 (transformer):** not run (MARBERT requires the project owner's approval).

## 5. External proxy: AURA-Classification v2 **human** labels
The gate was applied to AURA-Cls reviews whose duplicate group is in neither train nor val (one per group; no AURA-Cls item was used for training). AURA `bug_report` is treated as a proxy for "technical complaint".

| subset | n | agreement | κ | precision vs bug_report | recall vs bug_report | predicted complaint rate: bug_report / improvement / others / rating |
|---|---|---|---|---|---|---|
| all domains | 2,604 | 0.836 | 0.604 | 0.654 | 0.797 | 0.80 / 0.26 / 0.14 / 0.12 |
| non-game | 1,732 | 0.836 | 0.629 | 0.675 | 0.842 | 0.84 / 0.29 / 0.14 / 0.13 |

The gate generalises to independently human-labelled data at a similar level. Lower precision mostly reflects improvement requests that mention a problem, which our guide counts as complaints (definition mismatch, not necessarily error).

## 6. Error analysis
- **TRANS is the weakest class** (recall 0.125; 6 of 8 test items were predicted OTHER). Train has only 34 TRANS items, and TRANS wording ("ما قدرت احجز", "اخذ الفلوس", "لا استطيع اضافة") is lexically diverse and overlaps OTHER.
- **OTHER is a confusion sink** in both directions (OTHER↔AVAIL 6+4, UX→OTHER 4, AUTH→OTHER 4). This is expected for a residual class.
- **UX recall 0.36:** design and navigation complaints are often phrased like generic problems.
- **Gate false negatives on paraphrases outside the training vocabulary.** Probes: "الـ OTP ما يوصلني when I try to login" got complaint_score 0.32 (missed and not flagged); "ما أقدر ألاقي زر حجز الموعد" got 0.23 (missed). Mixed Arabic/English and UX "can't find" phrasing are under-represented in AURA.
- Probes handled correctly: "رمز التحقق لا يصل عند تسجيل الدخول" → AUTH (0.89), "التطبيق يقفل فجأة لما أفتح الطلب" → AVAIL, "خصم المبلغ وما اكتمل الطلب" → TRANS (flagged for review), "التطبيق بطيء" → PERF (flagged), praise → not complaint.

## 7. Limitations
AI-assisted reference labels (§ top); small PERF/TRANS samples; public store reviews only (short, no dates). Generalisation to e-mails, tickets, and OCR text is **untested**. Domain mix is wider than Saudi e-government (1,000 of 2,000 items are government apps). The single validation set is small, so model selection is noisy, but the test estimate is unbiased because test was used once. No guarantee of accuracy on other channels.
