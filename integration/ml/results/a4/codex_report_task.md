# A4 report renderer task notes

## Scope and file ownership

Work was confined to the requested A4 worktree. The implementation files are
`scripts/a4_report.py` and `tests/test_a4_report.py`; this document records the work.
The renderer writes only the authorized `reports/a4_report.md`,
`reports/a4_model_card.md`, and `reports/a4_annotation_provenance.md` outputs.

The existing modification to `scripts/a4_experiments.py` and the untracked
`results/a4/logs/marbert_chain.log` were present before this task and were left
alone. No training, selection, evaluation, inference, model loading, git commit,
or process management was performed.

## Inspected evidence and schemas

- Read the saved selection protocol in `configs/a4_selection_rule.yaml`.
- Inspected `results/a4/agreement_a4.json`, `results/a4/sampling_flow.json`,
  `data/a4/split_a4_info.json`, and `results/a4/label_issues_summary.json`.
- Inspected available `results/a4/runs/*/metrics_val.json` files, which store
  macro-F1 values, TRANS/UX recall, evaluated count, and per-class summaries.
  Transformer metadata fields are optional and are displayed when present.
- Selection, holdout metrics, and export manifests were absent at initial
  inspection. Read their producer source code to establish the actual output
  schema, without importing or executing any producer script. The renderer uses
  the recorded `selected`, `decision_log`, `validation_table`, `families`,
  `candidates`, `export_dir`, and model-version fields and the evaluator's exact
  subset, review, confidence interval, external proxy, and cost keys.
- Inspected the parquet schema first, then projected only provenance columns:
  `set`, `stratum`, coder/adjudicator model identifiers, `guide_version`,
  `adjudicated`, `modified_in_a4`, and `synthetic_verified`.
- The split CSV contains label values, so the renderer explicitly requests only
  `set` and `a4_split`. This membership projection establishes the baseline's
  validation overlap without accessing label values.

No per-item holdout label values, holdout errors, confusion files, holdout sample,
or holdout predictions were accessed. Existing JSON aggregate summaries are
reported as supplied, without recalculating holdout metrics.

## Implementation

`main(root=..., out_dir=...)` supports the real worktree and isolated temporary
test inputs. It returns success after writing all three reports. Missing files,
optional keys, null mappings, unavailable provenance columns, and incomplete JSON
results produce pending markers. Missing/unreadable sources also print a pending
line. The renderer performs no selection, model export, score calculation,
bootstrap, or cost measurement.

The main report includes the purpose and linked protocol, the saved protocol
text, all four data/annotation sources, every available validation run, baseline
contamination derived from split membership, the saved selection decision log,
and all requested evaluation tables. Evaluation includes each candidate's four
holdout subsets, review rate/automatic coverage/accuracy, selected and baseline
per-class category precision/recall/F1, saved confidence intervals and paired
selected-minus-baseline delta, external AURA proxy, selected-export cost, and an
explicitly non-blind v1-test section. Fixed caveats are included. Synthetic
verification counts are read from the agreement JSON rather than hardcoded.

The model card resolves a unique matching manifest by the recorded export path,
model version, and selected candidate when available. It never guesses the
latest directory. It reports export identity/files/backend, label provenance,
categories, thresholds, score semantics, selection evidence, saved selected-model
evaluation, and limitations. Missing or ambiguous export evidence remains pending.

The annotation report groups provenance by original annotation set, counts
adjudications and modifications, reports adjudicated rates over non-null boolean
flags, and tabulates stored model identifiers and guide versions. Its change
table comes from the precomputed v1 train/validation re-review summary; no label
columns are needed. Synthetic verification is summarized from both saved JSON
and provenance metadata by synthetic stratum.

All reported data numbers come from input files or metadata aggregation. The
historical v1 numbers in the explicitly requested fixed caveat are the only
literal performance numbers in the production renderer. Test fixture values are
fabricated summaries and are clearly identified as such.

## Verification

Tests cover real-file rendering and required headers, provenance-only parquet
and CSV projections, missing selection and holdout files separately and together,
partial metadata and in-progress malformed JSON, the exact published evaluation
schema using fabricated summaries, correct selected-export resolution, ambiguous
exports, and annotation modification/adjudication counts with missing columns.

The script and requested pytest file were each invoked once. Bytecode and pytest
cache writes were disabled to keep incidental files out of the worktree.

Renderer command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.. .venv/bin/python scripts/a4_report.py
```

Result: exit status 0; all three authorized Markdown reports were written.
The missing selection and holdout JSON inputs printed pending lines, and the
selected-export card also displays the missing manifest as pending.

Requested test command (with only cache/bytecode suppression added to the environment):

```sh
export PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider'
.venv/bin/pytest -q tests/test_a4_report.py
```

Result: exit status 0; **8 passed in 0.53s**. No failures or reruns were required.

Read back the generated reports to verify the protocol link, validation table,
198/815 baseline contamination note, pending selection/holdout/export sections,
32 modified-label total and transition table, stored guide/model provenance,
300/300 synthetic verification, and fixed caveats. These values were sourced from
the evidence described above rather than entered into the renderer.

The background experiment produced the new
`results/a4/runs/E3_marbert_lr2e-05_ce_s42/` directory during this task. The renderer
included its available validation summary, including temperature, training
minutes, and best epoch; the directory was neither created nor modified by this
task. The report is a snapshot of evidence available during its single render.
Selection, holdout results, and the selected export remain pending because their
source files are not yet present. There are no known implementation or test
failures.
