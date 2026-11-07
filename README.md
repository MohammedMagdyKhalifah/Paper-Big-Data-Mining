# Paper: Big Data Mining

Research project for detecting and categorising Arabic technical complaints, with a local web dashboard, machine-learning experiments, and OCR-based screenshot analysis.

## Project structure

| Path | Contents |
| --- | --- |
| `integration/` | Latest combined application and ML implementation, including A4/MARBERT and P1 OCR. Start here for the integrated system. |
| `integration/app/` | React/TypeScript dashboard, FastAPI backend, tests, dependency locks, model receipts, and verification evidence. |
| `integration/ml/` | Inference and training code, experiment configurations, annotations, split manifests, evaluation results, and reports. |
| `app/` | Earlier standalone dashboard implementation, preserved for project history. |
| `ml/` | Earlier standalone ML baseline, preserved for project history. |
| `docs/research/` | Six research summaries copied from the separate documentation worktree. |
| Root planning documents | Original implementation and research plans, including the Arabic project plan. |

The `app/`, `ml/`, and `integration/` folders originated as separate local Git repositories. This upload preserves their current file contents as ordinary folders; their nested Git databases and duplicate development worktrees are excluded.

## Running the application

For the latest integrated system, change into `integration/` first. Follow [P1 setup](integration/app/P1_SETUP.md), the [application README](integration/app/README.md), and the [environment setup guide](integration/app/ENVIRONMENT_SETUP.md). Commands in those documents assume that `integration/` is the working directory.

The earlier standalone dashboard can run in its default mock mode without trained ML weights; follow [its README](app/README.md) from this repository's root.

Dependency specifications and lockfiles are included. Installed Python environments, Node dependencies, build outputs, wheel caches, local `.env` files, SQLite databases, and runtime uploads are excluded. Copy the provided [configuration example](integration/app/.env.example) when configuring the integrated application.

## Model assets and data

Trained model weights and downloaded OCR weights are excluded, including `.joblib` and `.safetensors` files. A fresh checkout therefore needs the model assets described in the setup guides before real inference works. Model manifests, export metadata, tokenizers, checksums, and asset receipts remain available for verification.

Raw downloaded datasets and intermediate corpora remain local. Acquisition and processing scripts, curated research annotations, split information, synthetic OCR fixtures, evaluation outputs, and research reports are included. Dataset sources and attribution are documented in the [data manifest](integration/ml/reports/data_manifest.md). Consult each report for annotation provenance and limitations.

## Research documentation

Start with [the project summary](docs/research/MASTER_PROJECT_SUMMARY.md), then consult the [ML methodology](docs/research/COMPLETE_ML_METHODOLOGY.md), [experimental results](docs/research/ALL_EXPERIMENTAL_RESULTS.md), [project history](docs/research/COMPLETE_PROJECT_HISTORY.md), [system implementation](docs/research/SYSTEM_IMPLEMENTATION_AND_P1.md), and [findings and limitations](docs/research/RESEARCH_FINDINGS_AND_LIMITATIONS.md).

These documents preserve their original worktree contents. Historical paths and branch references describe the local development layout; detailed reports and verification records remain in `integration/`.
