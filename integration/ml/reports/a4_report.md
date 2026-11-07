# A4 report

## Purpose and protocol

Document A4 data, annotation, validation comparisons, the recorded selection and subsequent evaluation using existing evidence only. Selection and review thresholds use validation; holdout evaluation follows frozen selection.

Protocol: [configs/a4_selection_rule.yaml](../configs/a4_selection_rule.yaml). The saved protocol is reproduced below.

```yaml
# A4 pre-registered experiment + selection protocol (committed BEFORE any A4 model is trained).
version: 1
frozen_holdout: data/a4/holdout_sample.parquet   # ids sha256 65fb9459... ; labels via guide v1.1, sonnet+fable+opus
holdout_use: "evaluated ONCE per candidate after selection is frozen in results/a4/selection.json; never used for tuning"
v1_test: "kept out of all A4 training; may be reported as a secondary, NON-blind comparison only"

splits:
  pool: "v1 train+val (labels after re-review) + 4,000 A4 training expansion"
  method: "StratifiedGroupKFold(n_splits=7, shuffle, seed 42) on label_final grouped by dup_group; 1 fold = A4 validation (~14%), rest = A4 train"
  synthetic: "TRAINING only (each synthetic item its own group); validation and holdout are real-only"

metrics_on_validation:
  primary: e2e_macro_f1        # 7-way: NO + six categories (UNCLEAR excluded)
  secondary: [gate_macro_f1, category_macro_f1, recall_TRANS, recall_UX]

candidates:
  E0_baseline_v1: "artifact tfidf-baseline-v1 unchanged (reference)"
  E1_tfidf_a4: "v1 architecture (two-stage char TF-IDF LR) re-tuned on A4 train/val, small grid"
  E2_tfidf_a4_synth: "E1 best config + synthetic training data"
  E3_marbert: "UBC-NLP/MARBERTv2 fine-tune, 7-way head; grid lr {2e-5,4e-5} x loss {ce, ce_sqrt_class_weights}; max 6 epochs, early stopping on val e2e macro-F1 (patience 2); best config re-run with 3 seeds"
  E4_marbert_synth: "E3 best config + synthetic (1 seed first; 3 seeds only if it wins on val)"
  E5_e5_lr: "intfloat/multilingual-e5-base frozen mean-pooled embeddings + LogisticRegression 7-way (C grid)"

selection_rule:
  - "rank candidates by validation e2e_macro_f1 (transformer: mean over 3 seeds)"
  - "a transformer replaces the TF-IDF candidate only if mean val e2e_macro_f1 gain >= 0.02 AND its gate_macro_f1 is not lower by more than 0.01"
  - "synthetic augmentation is retained only if it improves val e2e_macro_f1 by >= 0.005 for the same architecture"
  - "ties (< 0.005) -> cheaper model"
  - "the selected seed/run for export = the seed with the median val e2e_macro_f1 among the 3 (not the best)"
thresholds: "needs_review thresholds chosen on validation for ~0.90 precision of automatic decisions (same rule as v1)"
```

## Data and annotation

### Annotation agreement

Source: `results/a4/agreement_a4.json`.

| Field | Recorded value |
| --- | --- |
| holdout.n | 1240 |
| holdout.complaint_kappa | 0.8727 |
| holdout.joint_kappa | 0.8429 |
| holdout.joint_pct_agree | 0.9000 |
| holdout.category_kappa_both_yes | 0.8804 |
| holdout.n_adjudicated | 124 |
| holdout.uncertain_rate | 0.3419 |
| holdout.final_distribution.NO | 714 |
| holdout.final_distribution.AVAIL | 151 |
| holdout.final_distribution.OTHER | 120 |
| holdout.final_distribution.AUTH | 104 |
| holdout.final_distribution.UX | 78 |
| holdout.final_distribution.TRANS | 50 |
| holdout.final_distribution.PERF | 14 |
| holdout.final_distribution.UNCLEAR | 9 |
| holdout.by_stratum.enr_codeswitch.NO | 26 |
| holdout.by_stratum.enr_codeswitch.AVAIL | 5 |
| holdout.by_stratum.enr_codeswitch.AUTH | 4 |
| holdout.by_stratum.enr_codeswitch.OTHER | 3 |
| holdout.by_stratum.enr_codeswitch.TRANS | 2 |
| holdout.by_stratum.enr_trans.NO | 98 |
| holdout.by_stratum.enr_trans.TRANS | 22 |
| holdout.by_stratum.enr_trans.UX | 10 |
| holdout.by_stratum.enr_trans.AVAIL | 10 |
| holdout.by_stratum.enr_trans.OTHER | 8 |
| holdout.by_stratum.enr_trans.PERF | 1 |
| holdout.by_stratum.enr_trans.UNCLEAR | 1 |
| holdout.by_stratum.enr_ux.NO | 68 |
| holdout.by_stratum.enr_ux.UX | 36 |
| holdout.by_stratum.enr_ux.OTHER | 12 |
| holdout.by_stratum.enr_ux.AVAIL | 11 |
| holdout.by_stratum.enr_ux.TRANS | 9 |
| holdout.by_stratum.enr_ux.AUTH | 9 |
| holdout.by_stratum.enr_ux.PERF | 3 |
| holdout.by_stratum.enr_ux.UNCLEAR | 2 |
| holdout.by_stratum.random.NO | 522 |
| holdout.by_stratum.random.AVAIL | 125 |
| holdout.by_stratum.random.OTHER | 97 |
| holdout.by_stratum.random.AUTH | 91 |
| holdout.by_stratum.random.UX | 32 |
| holdout.by_stratum.random.TRANS | 17 |
| holdout.by_stratum.random.PERF | 10 |
| holdout.by_stratum.random.UNCLEAR | 6 |
| a4_train.n | 4000 |
| a4_train.complaint_kappa | 0.8706 |
| a4_train.joint_kappa | 0.8392 |
| a4_train.joint_pct_agree | 0.9030 |
| a4_train.category_kappa_both_yes | 0.8789 |
| a4_train.n_adjudicated | 388 |
| a4_train.uncertain_rate | 0.3397 |
| a4_train.final_distribution.NO | 2449 |
| a4_train.final_distribution.OTHER | 394 |
| a4_train.final_distribution.AVAIL | 361 |
| a4_train.final_distribution.AUTH | 311 |
| a4_train.final_distribution.UX | 202 |
| a4_train.final_distribution.TRANS | 198 |
| a4_train.final_distribution.UNCLEAR | 56 |
| a4_train.final_distribution.PERF | 29 |
| a4_train.by_stratum.enr_codeswitch.NO | 43 |
| a4_train.by_stratum.enr_codeswitch.AVAIL | 6 |
| a4_train.by_stratum.enr_codeswitch.AUTH | 5 |
| a4_train.by_stratum.enr_codeswitch.OTHER | 3 |
| a4_train.by_stratum.enr_codeswitch.TRANS | 1 |
| a4_train.by_stratum.enr_codeswitch.UX | 1 |
| a4_train.by_stratum.enr_codeswitch.PERF | 1 |
| a4_train.by_stratum.enr_trans.NO | 461 |
| a4_train.by_stratum.enr_trans.TRANS | 102 |
| a4_train.by_stratum.enr_trans.OTHER | 43 |
| a4_train.by_stratum.enr_trans.AUTH | 30 |
| a4_train.by_stratum.enr_trans.UX | 29 |
| a4_train.by_stratum.enr_trans.AVAIL | 25 |
| a4_train.by_stratum.enr_trans.UNCLEAR | 6 |
| a4_train.by_stratum.enr_trans.PERF | 4 |
| a4_train.by_stratum.enr_ux.NO | 146 |
| a4_train.by_stratum.enr_ux.UX | 69 |
| a4_train.by_stratum.enr_ux.OTHER | 22 |
| a4_train.by_stratum.enr_ux.AVAIL | 16 |
| a4_train.by_stratum.enr_ux.AUTH | 15 |
| a4_train.by_stratum.enr_ux.TRANS | 5 |
| a4_train.by_stratum.enr_ux.PERF | 3 |
| a4_train.by_stratum.model_pred_trans_ux.NO | 120 |
| a4_train.by_stratum.model_pred_trans_ux.OTHER | 40 |
| a4_train.by_stratum.model_pred_trans_ux.TRANS | 37 |
| a4_train.by_stratum.model_pred_trans_ux.UX | 27 |
| a4_train.by_stratum.model_pred_trans_ux.AVAIL | 10 |
| a4_train.by_stratum.model_pred_trans_ux.AUTH | 5 |
| a4_train.by_stratum.model_pred_trans_ux.UNCLEAR | 3 |
| a4_train.by_stratum.model_pred_trans_ux.PERF | 2 |
| a4_train.by_stratum.model_uncertain_gate.NO | 241 |
| a4_train.by_stratum.model_uncertain_gate.OTHER | 47 |
| a4_train.by_stratum.model_uncertain_gate.AVAIL | 21 |
| a4_train.by_stratum.model_uncertain_gate.AUTH | 14 |
| a4_train.by_stratum.model_uncertain_gate.UX | 12 |
| a4_train.by_stratum.model_uncertain_gate.UNCLEAR | 8 |
| a4_train.by_stratum.model_uncertain_gate.PERF | 4 |
| a4_train.by_stratum.model_uncertain_gate.TRANS | 3 |
| a4_train.by_stratum.random.NO | 999 |
| a4_train.by_stratum.random.AVAIL | 248 |
| a4_train.by_stratum.random.AUTH | 213 |
| a4_train.by_stratum.random.OTHER | 199 |
| a4_train.by_stratum.random.UX | 56 |
| a4_train.by_stratum.random.TRANS | 42 |
| a4_train.by_stratum.random.UNCLEAR | 29 |
| a4_train.by_stratum.random.PERF | 14 |
| a4_train.by_stratum.random_topup.NO | 439 |
| a4_train.by_stratum.random_topup.OTHER | 40 |
| a4_train.by_stratum.random_topup.AVAIL | 35 |
| a4_train.by_stratum.random_topup.AUTH | 29 |
| a4_train.by_stratum.random_topup.UNCLEAR | 10 |
| a4_train.by_stratum.random_topup.TRANS | 8 |
| a4_train.by_stratum.random_topup.UX | 8 |
| a4_train.by_stratum.random_topup.PERF | 1 |
| synthetic.n_generated | 300 |
| synthetic.n_verified | 300 |
| synthetic.verified_by_kind.syn_codeswitch | 1.0000 |
| synthetic.verified_by_kind.syn_hard_negative | 1.0000 |
| synthetic.verified_by_kind.syn_trans | 1.0000 |
| synthetic.verified_by_kind.syn_ux | 1.0000 |
| v1_rereview.n_flagged_train_val | 239 |
| v1_rereview.blind_agreed | 200 |
| v1_rereview.adjudicated | 39 |
| v1_rereview.label_changed | 32 |
| v1_rereview.changes.AUTH->NO | 1 |
| v1_rereview.changes.AVAIL->NO | 1 |
| v1_rereview.changes.AVAIL->OTHER | 11 |
| v1_rereview.changes.NO->AUTH | 1 |
| v1_rereview.changes.NO->UNCLEAR | 1 |
| v1_rereview.changes.OTHER->AUTH | 1 |
| v1_rereview.changes.OTHER->NO | 1 |
| v1_rereview.changes.OTHER->TRANS | 1 |
| v1_rereview.changes.OTHER->UNCLEAR | 1 |
| v1_rereview.changes.OTHER->UX | 1 |
| v1_rereview.changes.PERF->AVAIL | 1 |
| v1_rereview.changes.PERF->NO | 2 |
| v1_rereview.changes.TRANS->NO | 1 |
| v1_rereview.changes.UX->AUTH | 1 |
| v1_rereview.changes.UX->NO | 1 |
| v1_rereview.changes.UX->OTHER | 6 |
| set_sizes.a4_train | 4000 |
| set_sizes.v1_train | 1399 |
| set_sizes.holdout | 1240 |
| set_sizes.v1_test | 301 |
| set_sizes.v1_val | 300 |
| set_sizes.synthetic | 300 |

### Sampling flow

Source: `results/a4/sampling_flow.json`.

| Field | Recorded value |
| --- | --- |
| pool | 17380 |
| pool_lex_trans | 1293 |
| pool_lex_ux | 526 |
| pool_code_switch | 126 |
| holdout.random | 900 |
| holdout.enr_ux | 150 |
| holdout.enr_trans | 150 |
| holdout.enr_codeswitch | 40 |
| holdout_domain.gov | 619 |
| holdout_domain.consumer_other | 466 |
| holdout_domain.commerce_delivery | 113 |
| holdout_domain.utility | 24 |
| holdout_domain.finance | 9 |
| holdout_domain.telecom | 9 |
| train_expansion.random | 1800 |
| train_expansion.enr_trans | 700 |
| train_expansion.random_topup | 570 |
| train_expansion.model_uncertain_gate | 350 |
| train_expansion.enr_ux | 276 |
| train_expansion.model_pred_trans_ux | 244 |
| train_expansion.enr_codeswitch | 60 |
| train_expansion_domain.gov | 1653 |
| train_expansion_domain.consumer_other | 1567 |
| train_expansion_domain.commerce_delivery | 577 |
| train_expansion_domain.utility | 136 |
| train_expansion_domain.telecom | 54 |
| train_expansion_domain.finance | 13 |
| holdout_ids_sha256 | 65fb9459108967c211e1fec0a4caa19b1629cc6368f5f34055670f4cc8bd07f5 |

### Split information

Source: `data/a4/split_a4_info.json`.

| Field | Recorded value |
| --- | --- |
| sha256 | 6719e22c9210186a7f9100f87e7f63d88bd2b8b57820e21d836896a744fd6a4a |
| counts.train | 4884 |
| counts.holdout | 1240 |
| counts.val | 815 |
| counts.v1_test | 301 |
| counts.train_synthetic | 300 |
| by_label.holdout.AUTH | 104 |
| by_label.holdout.AVAIL | 151 |
| by_label.holdout.NO | 714 |
| by_label.holdout.OTHER | 120 |
| by_label.holdout.PERF | 14 |
| by_label.holdout.TRANS | 50 |
| by_label.holdout.UNCLEAR | 9 |
| by_label.holdout.UX | 78 |
| by_label.train.AUTH | 410 |
| by_label.train.AVAIL | 488 |
| by_label.train.NO | 2921 |
| by_label.train.OTHER | 508 |
| by_label.train.PERF | 48 |
| by_label.train.TRANS | 205 |
| by_label.train.UNCLEAR | 78 |
| by_label.train.UX | 226 |
| by_label.train_synthetic.AUTH | 14 |
| by_label.train_synthetic.AVAIL | 14 |
| by_label.train_synthetic.NO | 60 |
| by_label.train_synthetic.OTHER | 13 |
| by_label.train_synthetic.PERF | 13 |
| by_label.train_synthetic.TRANS | 103 |
| by_label.train_synthetic.UNCLEAR | 0 |
| by_label.train_synthetic.UX | 83 |
| by_label.v1_test.AUTH | 29 |
| by_label.v1_test.AVAIL | 39 |
| by_label.v1_test.NO | 168 |
| by_label.v1_test.OTHER | 34 |
| by_label.v1_test.PERF | 6 |
| by_label.v1_test.TRANS | 8 |
| by_label.v1_test.UNCLEAR | 6 |
| by_label.v1_test.UX | 11 |
| by_label.val.AUTH | 68 |
| by_label.val.AVAIL | 82 |
| by_label.val.NO | 487 |
| by_label.val.OTHER | 85 |
| by_label.val.PERF | 8 |
| by_label.val.TRANS | 34 |
| by_label.val.UNCLEAR | 14 |
| by_label.val.UX | 37 |

### Label issues

Source: `results/a4/label_issues_summary.json`.

| Field | Recorded value |
| --- | --- |
| n_scanned | 1665 |
| n_flagged | 239 |
| flagged_by_given_label.OTHER | 77 |
| flagged_by_given_label.AVAIL | 41 |
| flagged_by_given_label.NO | 37 |
| flagged_by_given_label.UX | 35 |
| flagged_by_given_label.TRANS | 19 |
| flagged_by_given_label.AUTH | 16 |
| flagged_by_given_label.PERF | 14 |
| flagged_given_to_pred.OTHER->NO | 38 |
| flagged_given_to_pred.OTHER->AVAIL | 30 |
| flagged_given_to_pred.AVAIL->NO | 21 |
| flagged_given_to_pred.UX->NO | 18 |
| flagged_given_to_pred.NO->AVAIL | 14 |
| flagged_given_to_pred.PERF->NO | 13 |
| flagged_given_to_pred.AVAIL->OTHER | 12 |
| flagged_given_to_pred.UX->OTHER | 10 |
| flagged_given_to_pred.TRANS->NO | 10 |
| flagged_given_to_pred.NO->AUTH | 9 |
| flagged_given_to_pred.NO->OTHER | 8 |
| flagged_given_to_pred.OTHER->AUTH | 7 |
| flagged_given_to_pred.AUTH->NO | 7 |
| flagged_given_to_pred.AUTH->AVAIL | 6 |
| flagged_given_to_pred.AVAIL->AUTH | 6 |
| flag_rate_adjudicated | 0.3347 |
| base_rate_adjudicated | 0.1748 |
| oof_macro_f1_7way | 0.4652 |

## Validation comparison

Source: `results/a4/runs/*/metrics_val.json`. All available runs are listed; missing fields are pending. `n` is the evaluated count recorded by each run; split counts include UNCLEAR, which the protocol excludes from scoring.

| Run | n | e2e_macro_f1 | gate_macro_f1 | category_macro_f1 | recall_TRANS | recall_UX | temperature | train_minutes | best_epoch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E0_baseline_v1 | 801 | 0.6446 | 0.8518 | 0.6654 | 0.5588 | 0.5135 | pending | pending | pending |
| E1_tfidf_a4 | 801 | 0.5961 | 0.8743 | 0.6757 | 0.6765 | 0.5135 | pending | pending | pending |
| E2_tfidf_a4_synth | 801 | 0.6051 | 0.8809 | 0.6771 | 0.6765 | 0.5946 | pending | pending | pending |
| E3_marbert_final_s13 | 801 | 0.7238 | 0.9291 | 0.7829 | 0.7647 | 0.6757 | 1.6500 | 3.1000 | 6 |
| E3_marbert_final_s42 | 801 | 0.6918 | 0.9140 | 0.7346 | 0.6176 | 0.5676 | 1.2000 | 4.0200 | 3 |
| E3_marbert_final_s7 | 801 | 0.7153 | 0.9113 | 0.7542 | 0.7353 | 0.7027 | 1.2000 | 2.7000 | 3 |
| E3_marbert_lr2e-05_ce_s42 | 801 | 0.5689 | 0.9190 | 0.5955 | 0.7353 | 0.5946 | 1.2500 | 3.9900 | 6 |
| E3_marbert_lr2e-05_ce_sqrt_class_weights_s42 | 801 | 0.6987 | 0.9212 | 0.7399 | 0.7647 | 0.6486 | 1.0000 | 3.2200 | 3 |
| E3_marbert_lr4e-05_ce_s42 | 801 | 0.6811 | 0.9230 | 0.7235 | 0.7059 | 0.6486 | 1.6500 | 3.3600 | 6 |
| E3_marbert_lr4e-05_ce_sqrt_class_weights_s42 | 801 | 0.6996 | 0.9125 | 0.7483 | 0.6471 | 0.7568 | 1.4000 | 3.2000 | 4 |
| E4_marbert_synth_s13 | 801 | 0.7108 | 0.9347 | 0.7419 | 0.6471 | 0.6216 | 1.7000 | 3.2600 | 6 |
| E4_marbert_synth_s42 | 801 | 0.7195 | 0.9223 | 0.7761 | 0.7353 | 0.6486 | 1.6500 | 5.8800 | 5 |
| E4_marbert_synth_s7 | 801 | 0.7306 | 0.9253 | 0.7672 | 0.6471 | 0.5946 | 1.7500 | 3.2100 | 6 |
| E5_e5_lr | 801 | 0.5144 | 0.8558 | 0.5929 | 0.6176 | 0.5946 | pending | pending | pending |

**E0_baseline_v1 validation is contaminated**: 198/815 val items were in v1 training (source: `data/a4/split_a4.csv`, membership columns only). Treat it as a reference; its validation score is unsuitable for an independent comparison.

## Selection decision log

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

## Holdout results

Source: `results/a4/holdout_metrics.json`. These are saved evaluation summaries; this renderer does not access holdout labels or recompute scores.

| Field | Recorded value |
| --- | --- |
| selected | E4_marbert_synth |
| model_version | a4-marbert-v1 |
| holdout_n_excl_unclear | 1231 |
| label_note | Reference labels are AI-assisted (sonnet+fable coders, opus adjudicator), NOT independent human ground truth. |

### Candidate metrics by holdout subset

| Candidate | Subset | n | e2e_macro_f1 | gate_macro_f1 | category_macro_f1 |
| --- | --- | --- | --- | --- | --- |
| E0_baseline_v1 | holdout_all | 1231 | 0.4890 | 0.8349 | 0.5407 |
| E0_baseline_v1 | holdout_random | 894 | 0.4777 | 0.8685 | 0.5130 |
| E0_baseline_v1 | holdout_enriched | 337 | 0.4292 | 0.7470 | 0.4849 |
| E0_baseline_v1 | holdout_codeswitch | 51 | 0.4275 | 0.8516 | 0.3837 |
| E1_tfidf_a4 | holdout_all | 1231 | 0.5868 | 0.8806 | 0.6341 |
| E1_tfidf_a4 | holdout_random | 894 | 0.5763 | 0.9034 | 0.6046 |
| E1_tfidf_a4 | holdout_enriched | 337 | 0.5548 | 0.8203 | 0.5971 |
| E1_tfidf_a4 | holdout_codeswitch | 51 | 0.5465 | 0.9364 | 0.5440 |
| E2_tfidf_a4_synth | holdout_all | 1231 | 0.5968 | 0.8830 | 0.6408 |
| E2_tfidf_a4_synth | holdout_random | 894 | 0.5682 | 0.8997 | 0.6043 |
| E2_tfidf_a4_synth | holdout_enriched | 337 | 0.5652 | 0.8392 | 0.6007 |
| E2_tfidf_a4_synth | holdout_codeswitch | 51 | 0.5418 | 0.8940 | 0.6095 |
| E3_marbert_final | holdout_all | 1231 | 0.7041 | 0.9024 | 0.7559 |
| E3_marbert_final | holdout_random | 894 | 0.6765 | 0.9161 | 0.7203 |
| E3_marbert_final | holdout_enriched | 337 | 0.7057 | 0.8662 | 0.7521 |
| E3_marbert_final | holdout_codeswitch | 51 | 0.6545 | 0.9190 | 0.6326 |
| E4_marbert_synth | holdout_all | 1231 | 0.6896 | 0.9125 | 0.7290 |
| E4_marbert_synth | holdout_random | 894 | 0.6713 | 0.9230 | 0.7139 |
| E4_marbert_synth | holdout_enriched | 337 | 0.6459 | 0.8848 | 0.6708 |
| E4_marbert_synth | holdout_codeswitch | 51 | 0.6585 | 0.9190 | 0.6387 |
| E5_e5_lr | holdout_all | 1231 | 0.5334 | 0.8369 | 0.5899 |
| E5_e5_lr | holdout_random | 894 | 0.5110 | 0.8557 | 0.5175 |
| E5_e5_lr | holdout_enriched | 337 | 0.5459 | 0.7871 | 0.6076 |
| E5_e5_lr | holdout_codeswitch | 51 | 0.3855 | 0.8432 | 0.5393 |

### Review and automatic decisions

| Candidate | Subset | review_rate | auto_coverage | auto_accuracy | auto_complaint_coverage |
| --- | --- | --- | --- | --- | --- |
| E0_baseline_v1 | holdout_all | 0.4029 | 0.5971 | 0.8844 | 0.2070 |
| E0_baseline_v1 | holdout_random | 0.3792 | 0.6208 | 0.9045 | 0.2186 |
| E0_baseline_v1 | holdout_enriched | 0.4659 | 0.5341 | 0.8222 | 0.1788 |
| E0_baseline_v1 | holdout_codeswitch | 0.2941 | 0.7059 | 0.8611 | 0.2353 |
| E1_tfidf_a4 | holdout_all | 0.3290 | 0.6710 | 0.9056 | 0.3145 |
| E1_tfidf_a4 | holdout_random | 0.3188 | 0.6812 | 0.9212 | 0.3075 |
| E1_tfidf_a4 | holdout_enriched | 0.3561 | 0.6439 | 0.8618 | 0.3333 |
| E1_tfidf_a4 | holdout_codeswitch | 0.2745 | 0.7255 | 0.9459 | 0.4118 |
| E2_tfidf_a4_synth | holdout_all | 0.3542 | 0.6458 | 0.9094 | 0.2259 |
| E2_tfidf_a4_synth | holdout_random | 0.3490 | 0.6510 | 0.9330 | 0.2234 |
| E2_tfidf_a4_synth | holdout_enriched | 0.3680 | 0.6320 | 0.8451 | 0.2324 |
| E2_tfidf_a4_synth | holdout_codeswitch | 0.3529 | 0.6471 | 0.9091 | 0.1176 |
| E3_marbert_final | holdout_all | 0.2275 | 0.7725 | 0.9043 | 0.5286 |
| E3_marbert_final | holdout_random | 0.2271 | 0.7729 | 0.9190 | 0.5144 |
| E3_marbert_final | holdout_enriched | 0.2285 | 0.7715 | 0.8654 | 0.5625 |
| E3_marbert_final | holdout_codeswitch | 0.2157 | 0.7843 | 0.9500 | 0.5000 |
| E4_marbert_synth | holdout_all | 0.2697 | 0.7303 | 0.9132 | 0.3591 |
| E4_marbert_synth | holdout_random | 0.2506 | 0.7494 | 0.9194 | 0.4027 |
| E4_marbert_synth | holdout_enriched | 0.3205 | 0.6795 | 0.8952 | 0.2448 |
| E4_marbert_synth | holdout_codeswitch | 0.3137 | 0.6863 | 0.9714 | 0.2727 |
| E5_e5_lr | holdout_all | 0.3428 | 0.6572 | 0.8739 | 0.3496 |
| E5_e5_lr | holdout_random | 0.3244 | 0.6756 | 0.8758 | 0.3902 |
| E5_e5_lr | holdout_enriched | 0.3917 | 0.6083 | 0.8683 | 0.2381 |
| E5_e5_lr | holdout_codeswitch | 0.2941 | 0.7059 | 0.8611 | 0.2308 |

### Per-class category precision / recall / F1

The following tables use `holdout_all.per_class_category` only.

#### E4_marbert_synth

| Category | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| AUTH | 0.8544 | 0.8462 | 0.8502 | 104 |
| AVAIL | 0.7933 | 0.7881 | 0.7907 | 151 |
| PERF | 0.6667 | 0.4286 | 0.5217 | 14 |
| TRANS | 0.7455 | 0.8200 | 0.7810 | 50 |
| UX | 0.8209 | 0.7051 | 0.7586 | 78 |
| OTHER | 0.6391 | 0.7083 | 0.6719 | 120 |

#### E0_baseline_v1

| Category | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| AUTH | 0.6532 | 0.7788 | 0.7105 | 104 |
| AVAIL | 0.6400 | 0.7417 | 0.6871 | 151 |
| PERF | 0.4000 | 0.2857 | 0.3333 | 14 |
| TRANS | 0.6364 | 0.4200 | 0.5060 | 50 |
| UX | 0.6939 | 0.4359 | 0.5354 | 78 |
| OTHER | 0.4603 | 0.4833 | 0.4715 | 120 |

### ci95_holdout_all — paired delta

Intervals are copied from the saved bootstrap results. The paired delta is selected minus baseline; no bootstrap is run here.

| Metric | Selected CI | Baseline CI | Paired delta: selected minus baseline CI |
| --- | --- | --- | --- |
| e2e_macro_f1 | [0.634, 0.7359] | [0.4368, 0.5359] | [0.1392, 0.2595] |
| gate_macro_f1 | [0.8959, 0.9283] | [0.8125, 0.8548] | [0.0557, 0.0998] |
| category_macro_f1 | [0.6678, 0.78] | [0.4779, 0.5957] | [0.1221, 0.2516] |

### external_aura_proxy

| Field | Recorded value |
| --- | --- |
| E0_baseline_v1.n | 2604 |
| E0_baseline_v1.agreement | 0.8356 |
| E0_baseline_v1.kappa | 0.6040 |
| E0_baseline_v1.precision_vs_bug_report | 0.6539 |
| E0_baseline_v1.recall_vs_bug_report | 0.7971 |
| E4_marbert_synth.n | 2604 |
| E4_marbert_synth.agreement | 0.8706 |
| E4_marbert_synth.kappa | 0.6883 |
| E4_marbert_synth.precision_vs_bug_report | 0.7081 |
| E4_marbert_synth.recall_vs_bug_report | 0.8642 |

AURA bug-report agreement is an external gate proxy, not a category benchmark.

### cost_selected_export

| Field | Recorded value |
| --- | --- |
| artifact_size_mb | 328.4000 |
| first_call_s | 3.0700 |
| latency_ms | 34.3100 |
| peak_rss_mb | 1534.3000 |
| device | CPU (Apple M2 Max) |

Latency note: latency measured through ml.infer.predict_text, one message at a time

### v1_test_NOT_BLIND — NON-BLIND secondary comparison

v1 test is a non-blind secondary comparison and is not evidence for selecting a candidate.

| Candidate | n | e2e_macro_f1 | gate_macro_f1 | category_macro_f1 |
| --- | --- | --- | --- | --- |
| E0_baseline_v1 | 295 | 0.5529 | 0.8449 | 0.5679 |
| E1_tfidf_a4 | 295 | 0.6386 | 0.8772 | 0.6335 |
| E2_tfidf_a4_synth | 295 | 0.6143 | 0.8558 | 0.6535 |
| E3_marbert_final | 295 | 0.7696 | 0.9069 | 0.8285 |
| E4_marbert_synth | 295 | 0.6964 | 0.8952 | 0.7665 |
| E5_e5_lr | 295 | 0.5845 | 0.8525 | 0.6260 |

## Caveats

- AI-assisted reference labels are not human gold.
- Holdout differs from v1 test, so v1 numbers 0.845/0.568/0.553 are not directly comparable.
- PERF has small n.
- Code-switching is rare.
- Synthetic verification: 300/300 by a blind verifier; synthetic examples are prototypical.
