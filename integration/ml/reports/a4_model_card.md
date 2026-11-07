# A4 model card

## Selected export

Intended use: complaint triage and complaint category assignment with a review path for uncertain decisions. This card describes the recorded selected export.

Source: `artifacts/a4/export/a4-marbert-v1/manifest.json`.

### Export identity and provenance

| Field | Recorded value |
| --- | --- |
| model_version | a4-marbert-v1 |
| backend | hf-7way |
| selected_candidate | E4_marbert_synth |
| artifact_run | E4_marbert_synth_s42 |
| created_utc | 2026-10-30T11:44:39+00:00 |
| code_commit | e643a583b0f7d1d0646816e6e2171fc86819412e |
| label_provenance | AI-assisted reference labels (A4: sonnet+fable coders, opus adjudicator; v1: sonnet+haiku+sonnet). NOT human gold. |
| categories | ["AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER"] |
| files.model_dir | model |

## Decision thresholds and score semantics

### Thresholds

| Field | Recorded value |
| --- | --- |
| gate_decision | 0.5000 |
| gate_review_low | 0.5000 |
| gate_review_high | 0.5000 |
| category_review | 0.9000 |
| precision_target | 0.9000 |

### Score semantics

| Field | Recorded value |
| --- | --- |
| complaint_score | 1 - P(NO) (hf-7way, temperature-scaled) or gate P(complaint) (sklearn) |
| category_score | P(category \| complaint) |
| needs_review | gate score in [gate_review_low, gate_review_high) or category_score &lt; category_review |

## Selection evidence

### Selection decision log

Source: `results/a4/selection.json`.

| Field | Recorded value |
| --- | --- |
| selected | E4_marbert_synth |
| model_version | a4-marbert-v1 |
| export_dir | artifacts/a4/export/a4-marbert-v1 |
| rule | configs/a4_selection_rule.yaml |
| decided_utc | 2026-10-30T11:44:39+00:00 |
| code_commit | e643a583b0f7d1d0646816e6e2171fc86819412e |
| holdout_used | false |

- classical candidate: E2_tfidf_a4_synth
- transformer candidate: E4_marbert_synth
- best non-fine-tuned candidate: E2_tfidf_a4_synth
- transformer gain +0.1152 (need >= 0.02), gate drop -0.0465 (need &lt;= 0.01) -> REPLACE
- SELECTED: E4_marbert_synth

### Selection validation table

| Field | Recorded value |
| --- | --- |
| E0_baseline_v1.e2e | 0.6446 |
| E0_baseline_v1.gate | 0.8518 |
| E0_baseline_v1.category | 0.6654 |
| E0_baseline_v1.trans_recall | 0.5588 |
| E0_baseline_v1.ux_recall | 0.5135 |
| E1_tfidf_a4.e2e | 0.5961 |
| E1_tfidf_a4.gate | 0.8743 |
| E1_tfidf_a4.category | 0.6757 |
| E1_tfidf_a4.trans_recall | 0.6765 |
| E1_tfidf_a4.ux_recall | 0.5135 |
| E2_tfidf_a4_synth.e2e | 0.6051 |
| E2_tfidf_a4_synth.gate | 0.8809 |
| E2_tfidf_a4_synth.category | 0.6771 |
| E2_tfidf_a4_synth.trans_recall | 0.6765 |
| E2_tfidf_a4_synth.ux_recall | 0.5946 |
| E5_e5_lr.e2e | 0.5144 |
| E5_e5_lr.gate | 0.8558 |
| E5_e5_lr.category | 0.5929 |
| E5_e5_lr.trans_recall | 0.6176 |
| E5_e5_lr.ux_recall | 0.5946 |
| E3_marbert_final.e2e | 0.7103 |
| E3_marbert_final.e2e_std | 0.0166 |
| E3_marbert_final.gate | 0.9181 |
| E3_marbert_final.category | 0.7572 |
| E3_marbert_final.trans_recall | 0.7059 |
| E3_marbert_final.ux_recall | 0.6487 |
| E3_marbert_final.median_seed_run | E3_marbert_final_s7 |
| E4_marbert_synth.e2e | 0.7203 |
| E4_marbert_synth.e2e_std | 0.0099 |
| E4_marbert_synth.gate | 0.9274 |
| E4_marbert_synth.category | 0.7617 |
| E4_marbert_synth.trans_recall | 0.6765 |
| E4_marbert_synth.ux_recall | 0.6216 |
| E4_marbert_synth.median_seed_run | E4_marbert_synth_s42 |

### Seed families and median export run

| Field | Recorded value |
| --- | --- |
| E3_marbert_final.runs | ["E3_marbert_final_s13", "E3_marbert_final_s42", "E3_marbert_final_s7"] |
| E3_marbert_final.e2e_per_seed.E3_marbert_final_s13 | 0.7238 |
| E3_marbert_final.e2e_per_seed.E3_marbert_final_s42 | 0.6918 |
| E3_marbert_final.e2e_per_seed.E3_marbert_final_s7 | 0.7153 |
| E3_marbert_final.e2e_mean | 0.7103 |
| E3_marbert_final.e2e_std | 0.0166 |
| E3_marbert_final.gate_mean | 0.9181 |
| E3_marbert_final.category_mean | 0.7572 |
| E3_marbert_final.trans_recall_mean | 0.7059 |
| E3_marbert_final.ux_recall_mean | 0.6487 |
| E3_marbert_final.median_seed_run | E3_marbert_final_s7 |
| E4_marbert_synth.runs | ["E4_marbert_synth_s13", "E4_marbert_synth_s42", "E4_marbert_synth_s7"] |
| E4_marbert_synth.e2e_per_seed.E4_marbert_synth_s13 | 0.7108 |
| E4_marbert_synth.e2e_per_seed.E4_marbert_synth_s42 | 0.7195 |
| E4_marbert_synth.e2e_per_seed.E4_marbert_synth_s7 | 0.7306 |
| E4_marbert_synth.e2e_mean | 0.7203 |
| E4_marbert_synth.e2e_std | 0.0099 |
| E4_marbert_synth.gate_mean | 0.9274 |
| E4_marbert_synth.category_mean | 0.7617 |
| E4_marbert_synth.trans_recall_mean | 0.6765 |
| E4_marbert_synth.ux_recall_mean | 0.6216 |
| E4_marbert_synth.median_seed_run | E4_marbert_synth_s42 |

### Candidate export runs, validation thresholds and review

| Field | Recorded value |
| --- | --- |
| E0_baseline_v1.artifact_run | E0_baseline_v1 |
| E0_baseline_v1.thresholds.gate_review_low | 0.4000 |
| E0_baseline_v1.thresholds.gate_review_high | 0.6000 |
| E0_baseline_v1.thresholds.category_review | 0.5500 |
| E0_baseline_v1.val_metrics_from_artifact | 0.6446 |
| E0_baseline_v1.val_review.review_rate | 0.3059 |
| E0_baseline_v1.val_review.auto_coverage | 0.6941 |
| E0_baseline_v1.val_review.auto_accuracy | 0.9191 |
| E0_baseline_v1.val_review.auto_complaint_coverage | 0.4261 |
| E1_tfidf_a4.artifact_run | E1_tfidf_a4 |
| E1_tfidf_a4.thresholds.gate_review_low | 0.4000 |
| E1_tfidf_a4.thresholds.gate_review_high | 0.6000 |
| E1_tfidf_a4.thresholds.category_review | 0.6750 |
| E1_tfidf_a4.val_metrics_from_artifact | 0.5961 |
| E1_tfidf_a4.val_review.review_rate | 0.3084 |
| E1_tfidf_a4.val_review.auto_coverage | 0.6916 |
| E1_tfidf_a4.val_review.auto_accuracy | 0.9007 |
| E1_tfidf_a4.val_review.auto_complaint_coverage | 0.3217 |
| E2_tfidf_a4_synth.artifact_run | E2_tfidf_a4_synth |
| E2_tfidf_a4_synth.thresholds.gate_review_low | 0.4250 |
| E2_tfidf_a4_synth.thresholds.gate_review_high | 0.5750 |
| E2_tfidf_a4_synth.thresholds.category_review | 0.7750 |
| E2_tfidf_a4_synth.val_metrics_from_artifact | 0.6051 |
| E2_tfidf_a4_synth.val_review.review_rate | 0.3358 |
| E2_tfidf_a4_synth.val_review.auto_coverage | 0.6642 |
| E2_tfidf_a4_synth.val_review.auto_accuracy | 0.9211 |
| E2_tfidf_a4_synth.val_review.auto_complaint_coverage | 0.2476 |
| E5_e5_lr.artifact_run | E5_e5_lr |
| E5_e5_lr.thresholds.gate_review_low | 0.3000 |
| E5_e5_lr.thresholds.gate_review_high | 0.7000 |
| E5_e5_lr.thresholds.category_review | 0.7750 |
| E5_e5_lr.val_metrics_from_artifact | 0.5144 |
| E5_e5_lr.val_review.review_rate | 0.3134 |
| E5_e5_lr.val_review.auto_coverage | 0.6866 |
| E5_e5_lr.val_review.auto_accuracy | 0.9018 |
| E5_e5_lr.val_review.auto_complaint_coverage | 0.3704 |
| E3_marbert_final.artifact_run | E3_marbert_final_s7 |
| E3_marbert_final.thresholds.gate_review_low | 0.5000 |
| E3_marbert_final.thresholds.gate_review_high | 0.5000 |
| E3_marbert_final.thresholds.category_review | 0.8500 |
| E3_marbert_final.val_metrics_from_artifact | 0.7157 |
| E3_marbert_final.val_review.review_rate | 0.2060 |
| E3_marbert_final.val_review.auto_coverage | 0.7940 |
| E3_marbert_final.val_review.auto_accuracy | 0.9245 |
| E3_marbert_final.val_review.auto_complaint_coverage | 0.5299 |
| E4_marbert_synth.artifact_run | E4_marbert_synth_s42 |
| E4_marbert_synth.thresholds.gate_review_low | 0.5000 |
| E4_marbert_synth.thresholds.gate_review_high | 0.5000 |
| E4_marbert_synth.thresholds.category_review | 0.9000 |
| E4_marbert_synth.val_metrics_from_artifact | 0.7195 |
| E4_marbert_synth.val_review.review_rate | 0.2322 |
| E4_marbert_synth.val_review.auto_coverage | 0.7678 |
| E4_marbert_synth.val_review.auto_accuracy | 0.9171 |
| E4_marbert_synth.val_review.auto_complaint_coverage | 0.3902 |

## Evaluation

| Subset | n | e2e_macro_f1 | gate_macro_f1 | category_macro_f1 |
| --- | --- | --- | --- | --- |
| holdout_all | 1231 | 0.6896 | 0.9125 | 0.7290 |
| holdout_random | 894 | 0.6713 | 0.9230 | 0.7139 |
| holdout_enriched | 337 | 0.6459 | 0.8848 | 0.6708 |
| holdout_codeswitch | 51 | 0.6585 | 0.9190 | 0.6387 |

### holdout_all review and automatic decisions

| Field | Recorded value |
| --- | --- |
| review_rate | 0.2697 |
| auto_coverage | 0.7303 |
| auto_accuracy | 0.9132 |
| auto_complaint_coverage | 0.3591 |

### ci95_holdout_all including paired delta

| Field | Recorded value |
| --- | --- |
| e2e_macro_f1.selected | [0.634, 0.7359] |
| e2e_macro_f1.baseline | [0.4368, 0.5359] |
| e2e_macro_f1.delta_selected_minus_baseline | [0.1392, 0.2595] |
| gate_macro_f1.selected | [0.8959, 0.9283] |
| gate_macro_f1.baseline | [0.8125, 0.8548] |
| gate_macro_f1.delta_selected_minus_baseline | [0.0557, 0.0998] |
| category_macro_f1.selected | [0.6678, 0.78] |
| category_macro_f1.baseline | [0.4779, 0.5957] |
| category_macro_f1.delta_selected_minus_baseline | [0.1221, 0.2516] |

### external_aura_proxy

| Field | Recorded value |
| --- | --- |
| n | 2604 |
| agreement | 0.8706 |
| kappa | 0.6883 |
| precision_vs_bug_report | 0.7081 |
| recall_vs_bug_report | 0.8642 |

### cost_selected_export

| Field | Recorded value |
| --- | --- |
| artifact_size_mb | 328.4000 |
| first_call_s | 3.0700 |
| latency_ms | 34.3100 |
| peak_rss_mb | 1534.3000 |
| device | CPU (Apple M2 Max) |

### v1_test_NOT_BLIND — NON-BLIND secondary comparison

| Metric | Recorded value |
| --- | --- |
| n | 295 |
| e2e_macro_f1 | 0.6964 |
| gate_macro_f1 | 0.8952 |
| category_macro_f1 | 0.7665 |
| e2e_accuracy | 0.8373 |
| recall_TRANS | 0.3750 |
| recall_UX | 0.6364 |

## Limitations and review

Review flags and thresholds must be interpreted with the recorded score semantics. The evidence does not establish human-gold accuracy or performance outside the sampled data.

## Caveats

- AI-assisted reference labels are not human gold.
- Holdout differs from v1 test, so v1 numbers 0.845/0.568/0.553 are not directly comparable.
- PERF has small n.
- Code-switching is rare.
- Synthetic verification: 300/300 by a blind verifier; synthetic examples are prototypical.
