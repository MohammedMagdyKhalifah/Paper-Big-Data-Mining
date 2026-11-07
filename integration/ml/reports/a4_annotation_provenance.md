# A4 annotation provenance

Source: `data/a4/labels_a4.parquet`, provenance columns only. Label-value and text columns are never read, including on holdout. Existing agreement JSON supplies the aggregate v1 re-review change table and synthetic verification summary.

## Counts per set and adjudication

| Set | Count | Adjudicated count | Adjudicated rate | modified_in_a4 count |
| --- | --- | --- | --- | --- |
| a4_train | 4000 | 388 | 0.0970 | 0 |
| holdout | 1240 | 124 | 0.1000 | 0 |
| synthetic | 300 | 0 | 0.0000 | 0 |
| v1_test | 301 | 68 | 0.2259 | 0 |
| v1_train | 1399 | 270 | 0.1930 | 25 |
| v1_val | 300 | 45 | 0.1500 | 7 |

Adjudicated rates use non-null boolean flags as the denominator; missing flags are pending. Counts describe the stored provenance, including inherited v1 annotations.

## Coder and adjudicator models

| Set | Role | Stored model | Count |
| --- | --- | --- | --- |
| a4_train | coder_a_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 4000 |
| a4_train | coder_b_model | Claude Fable 5.1 (claude-fable-5-1) | 4000 |
| a4_train | adjudicator_model | Claude Opus 5.5 (claude-opus-5-5) | 4000 |
| holdout | coder_a_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 1240 |
| holdout | coder_b_model | Claude Fable 5.1 (claude-fable-5-1) | 1240 |
| holdout | adjudicator_model | Claude Opus 5.5 (claude-opus-5-5) | 1240 |
| synthetic | coder_a_model | generator intent: Claude Sonnet 5.5 (claude-sonnet-5-5) | 300 |
| synthetic | coder_b_model | blind verifier: Claude Fable 5.1 (claude-fable-5-1) | 300 |
| synthetic | adjudicator_model | pending | 300 |
| v1_test | coder_a_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 301 |
| v1_test | coder_b_model | Claude Haiku 4.5 (claude-haiku-4-5-20251001) | 301 |
| v1_test | adjudicator_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 301 |
| v1_train | coder_a_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 1399 |
| v1_train | coder_b_model | Claude Haiku 4.5 (claude-haiku-4-5-20251001) | 1399 |
| v1_train | adjudicator_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 1399 |
| v1_val | coder_a_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 300 |
| v1_val | coder_b_model | Claude Haiku 4.5 (claude-haiku-4-5-20251001) | 300 |
| v1_val | adjudicator_model | Claude Sonnet 5.5 (claude-sonnet-5-5) | 300 |

A pending adjudicator model may be null for synthetic items with a blind verifier; a stored adjudicator model does not imply that every item was adjudicated.

## Guide versions

| Set | guide_version | Count |
| --- | --- | --- |
| a4_train | v1.1 | 4000 |
| holdout | v1.1 | 1240 |
| synthetic | v1.1 | 300 |
| v1_test | v1.0 | 301 |
| v1_train | v1.0 | 1367 |
| v1_train | v1.1 (re-adjudicated) | 32 |
| v1_val | v1.0 | 293 |
| v1_val | v1.1 (re-adjudicated) | 7 |

## modified_in_a4 and change table

| Field | Count |
| --- | --- |
| modified_in_a4 | 32 |

Source for label transitions: `results/a4/agreement_a4.json`, `v1_rereview.changes` (precomputed v1 train/validation re-review only). No per-item labels are accessed.

| Change (v1 to A4) | Count |
| --- | --- |
| AUTH->NO | 1 |
| AVAIL->NO | 1 |
| AVAIL->OTHER | 11 |
| NO->AUTH | 1 |
| NO->UNCLEAR | 1 |
| OTHER->AUTH | 1 |
| OTHER->NO | 1 |
| OTHER->TRANS | 1 |
| OTHER->UNCLEAR | 1 |
| OTHER->UX | 1 |
| PERF->AVAIL | 1 |
| PERF->NO | 2 |
| TRANS->NO | 1 |
| UX->AUTH | 1 |
| UX->NO | 1 |
| UX->OTHER | 6 |

### v1 re-review summary

| Field | Recorded value |
| --- | --- |
| n_flagged_train_val | 239 |
| blind_agreed | 200 |
| adjudicated | 39 |
| label_changed | 32 |

## Synthetic verification

### Saved verification summary

Source: `results/a4/agreement_a4.json:synthetic`.

| Field | Recorded value |
| --- | --- |
| n_generated | 300 |
| n_verified | 300 |
| verified_by_kind.syn_codeswitch | 1.0000 |
| verified_by_kind.syn_hard_negative | 1.0000 |
| verified_by_kind.syn_trans | 1.0000 |
| verified_by_kind.syn_ux | 1.0000 |

| Synthetic stratum | Count | Verified count | Verified rate |
| --- | --- | --- | --- |
| syn_codeswitch | 80 | 80 | 1.0000 |
| syn_hard_negative | 60 | 60 | 1.0000 |
| syn_trans | 90 | 90 | 1.0000 |
| syn_ux | 70 | 70 | 1.0000 |

Synthetic generator intent and blind verifier identities are recorded in the model table above. Verification agreement does not make these prototypical examples human gold.

## Caveats

- AI-assisted reference labels are not human gold.
- Holdout differs from v1 test, so v1 numbers 0.845/0.568/0.553 are not directly comparable.
- PERF has small n.
- Code-switching is rare.
- Synthetic verification: 300/300 by a blind verifier; synthetic examples are prototypical.
