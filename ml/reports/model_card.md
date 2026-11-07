# Model Card — `tfidf-baseline-v1`

| | |
|---|---|
| Task | (1) Is an Arabic app/service message a **technical complaint**? (2) If so, its **primary category**: AUTH, AVAIL, PERF, TRANS, UX, OTHER |
| Interface | `ml.infer.predict_text(text) -> dict` (frozen contract, see `README.md`) |
| Artifacts | `artifacts/gate.joblib`, `artifacts/category.joblib`, `artifacts/manifest.json` |
| Runtime | local CPU, offline; scikit-learn 1.9.1, numpy, scipy, joblib; about 1.2 ms/message |
| Training data | 2,000 AURA app reviews (MIT); train split 1,399 (586 complaints) |
| Labels | AI-assisted reference labels: two independent Claude coders + adjudicator (inter-coder κ 0.78 complaint / 0.74 category; agreement with AURA human `bug_report` κ 0.72) |

## Architecture
Both models are sklearn `Pipeline`s. Preprocessing runs inside them, so raw text goes in.
1. **Gate:** `FunctionTransformer(P1 normalisation + PII masking)` → `TfidfVectorizer(char_wb, 2–5, min_df=1, sublinear_tf)` → `LogisticRegression(C=10, class_weight=balanced)`.
2. **Category:** same P1 → `TfidfVectorizer(char_wb, 2–5, min_df=2)` → `CalibratedClassifierCV(LogisticRegression(C=1, balanced), sigmoid, cv=5)` (calibration folds come from train only).
Selection was by validation macro-F1 over 96 + 192 configurations (`results/experiment_register.csv`).

## Outputs and their meaning
| key | meaning |
|---|---|
| `complaint_score` | Gate probability that the text is a technical complaint (raw LR `predict_proba`). Validation Brier 0.097, ECE 0.074. |
| `is_complaint` | `complaint_score ≥ 0.5` |
| `category` | argmax of the calibrated category model. Only set when `is_complaint` is true, otherwise `None`. |
| `category_score` | Calibrated top-class probability (validation ECE 0.137). `None` for non-complaints. |
| `needs_review` | `True` if `0.40 ≤ complaint_score < 0.60` **or** `category_score < 0.675`. Thresholds were chosen on validation so that **automatic** decisions reach about 90% precision. |
| `model_version` | `tfidf-baseline-v1` |

The scores are model confidences, **not** accuracy guarantees. `OTHER` is a content category; it never means "not a complaint" or "unsure".

## Performance (held-out test, vs reference labels; details in `evaluation.md`)
| | macro-F1 | Dummy | notes |
|---|---|---|---|
| Gate (n=295) | **0.845** (CI 0.80–0.88) | 0.363 | complaint P 0.82 / R 0.83 |
| Category (n=127) | **0.568** (CI 0.45–0.66) | 0.078 | AUTH 0.77, AVAIL 0.81, PERF 0.67 (n=6), OTHER 0.53, UX 0.44, TRANS 0.18 (n=8) |
| End-to-end (n=295) | 0.553 | | 38% flagged `needs_review`; accuracy on the unflagged messages 0.90 |
| Gate vs AURA human labels (n=2,604, external) | | | agreement 0.84, κ 0.60 |

## Intended use
- A triage aid: route or aggregate Arabic complaints by symptom family, with uncertain cases sent to human review.
- **Not** for diagnosing root causes, confirming outages, or automated replies. It does **not** identify which system or app a message refers to (that is Codex's separate component).

## Known weaknesses
- TRANS (payment/transaction) recall is low (0.125 on 8 test items) and UX recall 0.36. Expect these to be under-detected. Rely on `needs_review` and human correction.
- Mixed Arabic/English and phrasings rare in app-store reviews can be missed with **confident** scores (e.g. "الـ OTP ما يوصلني when I try to login" → not complaint, 0.32).
- Trained on short public store reviews. Performance on e-mails, long messages, or OCR output is **untested** and likely lower.
- Domain: about half of the training items are Saudi government apps. The rest are diverse consumer apps (games excluded).

## Ethics and privacy
Inputs are PII-masked inside the pipeline (phones, e-mails, URLs, long numbers). No personal data is stored in artifacts beyond TF-IDF vocabulary n-grams learned from public reviews.

## Reproduce
See `README.md` (`train.py` → `evaluate.py`; the evaluation rerun prints `REPRODUCTION CHECK: identical metrics`).
