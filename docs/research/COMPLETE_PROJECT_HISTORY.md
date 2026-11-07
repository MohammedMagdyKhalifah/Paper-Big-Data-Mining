# Complete Project History

**Project:** *Beyond Sentiment: Mining Actionable Service Failures from Arabic Digital Service Complaints Using Machine Learning*

**Document role:** the chronological, evidence-based history of every phase: what was planned, what was built, the decisions taken, the problems met and the resulting status.
* Methods: `COMPLETE_ML_METHODOLOGY.md`.
* Numbers: `ALL_EXPERIMENTAL_RESULTS.md`.
* Application: `SYSTEM_IMPLEMENTATION_AND_P1.md`.

**Evidence tags.**
* **[V]**: verified in this audit (2026-11-07) from Git objects or files.
* **[R]**: reported in a project progress or verification record, not re-executed.
* **[P]**: planned only.
* **[I]**: interpretation.

**Timestamps.** Commit timestamps (+0300) are *commit* times. Several phases were committed in quick succession, so commit times do not measure working duration [I].

---

## 1. Repositories, branches and worktrees (inspected 2026-11-07) [V]

| Repository (path under `Project/`) | Branch | HEAD | Role |
|---|---|---|---|
| `ml/` (Claude) | `agent/claude-ml` | `80511e7` | P0 ML: v1 baseline (A0–A3); tag `baseline-v1` = `a02d2fa` |
| `ml/.worktrees/a4/ml` | `agent/claude-ml-a4` | `aa4b394` | A4 improvement study |
| `ml/.worktrees/p1/ml` | `agent/claude-ml-p1` | `af72c54` | P1 OCR + system identification; evidence dossier |
| `ml/.worktrees/docs/ml` (sparse) | `agent/claude-docs` | this audit's commit | documentation-only branch (this file) |
| `app/` (Codex) | `agent/codex-app` | `e034f9b` | P0 web application, Mock predictor |
| `integration/` (Codex) | `integration/real-ml` | `d835a86` | app + v1 model integration |
| | `integration/a4-marbert` | `01f0b43` | app + A4 MARBERT integration |
| | `integration/a4-environment` | `3b2c2cf` | standalone hash-locked A4 environment (**latest fully verified integrated baseline**) |
| | `integration/p1` (checked out) | `071716d` | P1 integrated (source cutoff `035f3eb`); academic implementation evidence |
| `code/` | — | — | empty |

* **Planning documents** (project root, not under version control):
  * `481013386_MohammedKhalifah_5102_A1-X.docx` (the proposal).
  * `PROJECT_IMPLEMENTATION_PLAN_AR.md`.
  * `CLAUDE_CODE_ML_RESEARCH_PLAN.md`.
  * `CODEX_APP_DASHBOARD_PLAN.md`.
* **How the integration repository was built.** It imports both the ML and app histories through unsquashed `git subtree` merges: `d44f8ce` (app), `8b1162c` (ml), `e7d8ee1` (A4) and `afd3bde` (P1). Codex verified that the subtree trees equal the source commit trees (`integration/app/PROGRESS.md`, I1; P1-1). [V/R]

---

## 2. Timeline

| When (2026, +0300) | Repository / branch | Commit | Event |
|---|---|---|---|
| Oct 22 | — | — | Proposal document dated (file timestamp) |
| Oct 29, 22:57–23:15 | root | — | Arabic implementation plan; Claude ML plan; Codex app plan |
| Oct 29, 23:32 | ml / agent/claude-ml | `17fb8f1` | A0 + A1 data prep: contract, text processing, dedup, guide |
| Oct 29, 23:39 | ml | `cefa9b3` | A1.7 pilot coded; guide v1.0 frozen; label/split/train/eval scripts |
| Oct 29, 23:44 | app / agent/codex-app | `ee28839`, `110157e` | P0 web application (Mock model) and its verification checkpoint |
| Oct 29, 23:44 | ml | `ea8eb74` | Calibrated category learners, pandas 3 fix, data manifest, leakage tests |
| Oct 29, 23:56 | ml | `93a5142` | Labels merged (2,000), agreement + blind audit, frozen split |
| Oct 30, 00:01 | ml | `7040c03` | **A2 complete**: `tfidf-baseline-v1`, one-time test evaluation, K-Means |
| Oct 30, 00:02 | app | `e034f9b` | Dashboard analytics refinement; Arabic/English interface |
| Oct 30, 00:03 | ml | `a02d2fa` | Deterministic retrain verified (tag `baseline-v1`) |
| Oct 30, 00:14–00:29 | integration / real-ml | `b646867` → `2d6072e`, `9a3f21f` | Subtree import; **real v1 model integrated** into the app |
| Oct 30, 00:23 | ml | `80511e7` | Ignore nested worktrees |
| Oct 30, 00:29 | ml / agent/claude-ml-a4 | `e3ccd24` | **A4 holdout frozen** (1,240; sha `65fb9459`); 4,000 expansion drawn; cleanlab scan |
| Oct 30, 00:30 | ml-a4 | `7341ed7` | Guide v1.1 frozen |
| Oct 30, 08:48 | ml-a4 | `e541832` | **Selection protocol pre-registered**; holdout labels; v1 re-review outputs |
| Oct 30, 13:44–13:54 | ml-a4 | `fe78589`, `5ae688a`, `32ee889`, `e2c8357` | Multi-backend infer; expansion labelled; synthetic verified; A4 split; TF-IDF/e5 validation runs; owner-requested pause before MARBERT |
| Oct 30, 13:45 | integration / real-ml | `d835a86` | English digits in both UI languages |
| Oct 30, 14:14 | ml-a4 | `e643a58` | A4 report renderer + tests (written by Codex) |
| Oct 30, 14:44:49 | ml-a4 | `2b15bc4` | **MARBERT grid + seeds; selection → E4 (`a4-marbert-v1`) committed before the holdout** |
| Oct 30, 14:48:19 | ml-a4 | `1d3cbfa` | **One-time holdout evaluation**; final A4 reports |
| Oct 30, 18:52 | ml-a4 | `aa4b394` | Export checksums, pinned inference requirements, integrity tests (Codex) |
| Oct 30, 19:10–19:44 | integration / a4-marbert | `e7d8ee1`, `03a006f`, `01f0b43` | **A4 integrated into the app**; browser and rollback verified |
| Oct 30, 20:09 | integration / a4-environment | `9ea34e0`, `3b2c2cf` | Self-contained, hash-locked A4 environment |
| Oct 31, 01:16 | ml / agent/claude-ml-p1 | `a3035f4` | P1: OCR adapters, synthetic OCR set, **system registry v1 frozen** |
| Oct 31, 01:23 | ml-p1 | `977f496` | P1: `analyze()` pipeline, error cues, mention annotation + evaluation |
| Oct 31, 01:30 | ml-p1 | `d8ffad4` | P1 reports, pinned requirements, Codex P1 tests (155 pass) |
| Oct 31, 01:34–01:59 | integration / p1 | `afd3bde`, `7175581`, `035f3eb` | **P1 integrated into the app**; host/browser acceptance blocked |
| Oct 31, 19:41 | ml-p1 | `af72c54` | ML academic evidence dossier (`reports/ACADEMIC_ML_EVIDENCE.md`) |
| Oct 31, 19:48 | integration / p1 | `071716d` | App academic implementation evidence (`integration/app/ACADEMIC_IMPLEMENTATION_EVIDENCE.md`) |
| Nov 7 | ml / agent/claude-docs | this commit | Complete project audit documentation (`docs/`) |

---

## 3. Phases

### Phase 0: Proposal and planning

* **Purpose.** Define RQ1–RQ5, H1–H5 and O1–O5 (proposal §1.1–1.3), and split the work into ML (Claude) and app (Codex) streams.
* **Planned** [P]:
  * Collect app-store reviews from at least two Saudi e-government apps, targeting about 1,200 adjudicated complaints.
  * Two human coders with 20% double-coding.
  * Dummy, TF-IDF + LR and TF-IDF + SVM on a reserved test set; preprocessing ablations, including aggressive stemming.
  * K-Means and near-duplicates.
  * An optional transformer.
  * An actionability rubric (H5).
* **Decisions made in planning.** These are recorded in the plan file `~/.claude/plans/twinkling-jumping-hamster.md` and `IMPLEMENTATION_PLAN.md`:
  * The runtime is local and offline only; the Claude API is never used for inference.
  * Claude subagents are used **only** as annotators: Sonnet + Haiku with an adjudicator, accepted by the owner as AI-assisted labelling.
  * Git is initialised inside `ml/` only.
  * The licensed AURA datasets are used because no permitted scraping source was available. This invokes the proposal's own fallback clause (§3.2).
  * A frozen contract between the streams: `ml.infer.predict_text(text) -> dict`, with 6 keys.
* **Status.** Complete.

### Phase P0-ML (A0–A3): v1 baseline (branch `agent/claude-ml`)

* **A0.** Skeleton, git, `.venv`, `infer.py` contract and tests. The first run gave 10 passed and 5 skipped (the skips awaited artifacts). One wrong test expectation was fixed: repeated-letter collapse maps `أإآ` → `ا` by design. [R]
* **A1: data.**
  * Download at pinned revisions.
  * Text processing: P0/P1 masking and normalisation.
  * Cross-corpus near-duplicate grouping.
  * Domain map (45 gov apps; games excluded).
  * A 2,000-item stratified sample (gov 1,000 / non-gov 700 / AURA-Cls 300).
  * Guide v1.0-draft.
* **A1: labelling.**
  * The 100-item pilot gave κ 0.740 (complaint) and 0.669 (joint), and led to guide v1.0.
  * Main labelling: 8 batches of about 238 items each, using a Workflow with 25 agents.
  * A blind Opus audit covered 180 items.
  * Agreement on all 2,000: complaint κ 0.781; 383 items were adjudicated.
* **A1.10: split frozen.** Train 1,399 / val 300 / test 301 (sha `451ab15d`).
* **A2: model.**
  * A 290-configuration grid, 82 s on CPU.
  * Selected models: gate P1 char_wb 2–5 LR (val 0.875) and category P1 char_wb 2–5 calibrated LR (val 0.600).
  * One-time test: gate **0.845**, category **0.568**, e2e 0.553.
  * Latency 1.2 ms. Tests: 20 passed.
* **A3: K-Means.** Silhouette ≤ 0.022 and NMI ≤ 0.070: weak structure. The MARBERT step (A3.2) was **blocked pending owner approval**.
* **Problems → resolutions** [R]:
  1. Coder B (Haiku) produced no pilot file. It was re-run with a strict prompt.
  2. Batch `main_05` was degenerate. It was quarantined, re-coded and re-adjudicated.
  3. pandas 3 Arrow strings broke `CalibratedClassifierCV` indexing. Fixed with `.to_numpy(dtype=str)`.
  4. pandas 3 `groupby.apply` dropped a column. Replaced with an explicit loop, and the regenerated batches were verified byte-identical.
  5. Uncalibrated LR gave ECE 0.60. Sigmoid calibration was adopted.
* **Decisions.**
  * The G2 gate variant (AURA bug_report training data) was dropped so that AURA-Cls stays a clean external check.
  * Labels are reported as AI-assisted reference labels.
* **Status.** **Complete** (`7040c03`, `a02d2fa`). [V]

### Phase P0-App: web application with a Mock model (repository `app/`, branch `agent/codex-app`)

* **Implemented** [R] (`app/PROGRESS.md`, checkpoints 1–9):
  * FastAPI routes, strict predictor schemas, a Mock/Real adapter, SQLAlchemy/SQLite, CSV ingestion with deduplication, a correction audit trail and filtered analytics.
  * Six React pages in an RTL shell, and the two-service launcher `dev.mjs`.
  * Later additions: an Arabic/English interface and richer dashboard analytics.
  * Tests: 29 backend tests passed at checkpoint 1, and the frontend test was fixed later.
* **Problems → resolutions** [R]:
  1. Direct pip network access failed, so wheels were downloaded and installed offline.
  2. The sandbox denied raw uvicorn port binding; the authorised npm launcher was used instead.
  3. A TanStack Query mutation test failed and was fixed.
* **Status.** Complete as P0 with the Mock model (`e034f9b`). [V]

### Phase I: real v1 model integrated into the app (`integration/real-ml`)

* **Implemented** [R]:
  * Subtree imports of both histories.
  * A `RealPredictor` calling `ml.infer.predict_text`, with startup warm-up, no Mock fallback and visible 503s.
  * Tests against the real artifacts.
  * Model-card pairing.
  * English digits.
* **Verified** [R]:
  * 70 tests passed (50 backend + 20 ML).
  * 15 Vitest tests passed and the production build passed.
  * A native-Chrome flow covering Arabic OTP → AUTH, praise → non-complaint and AURA CSV import/reimport.
  * Dashboard figures agreed with SQL, and records persisted across a restart.
* **Problems → resolutions** [R]:
  1. A Vite fonts 403 came from a symlinked `node_modules`; it was replaced with an independent copy.
  2. A duplicate `node_modules 2` path made Vitest discover dependency suites and stalled Tailwind's scan; both were restricted to `src`.
  3. Two presentation fixes: `needs_review = false` ≠ "human reviewed", and Demo ≠ Mock.
* **Known model limitation surfaced.** The mixed-language OTP complaint was rated not-complaint by v1 (0.3165).
* **Status.** Complete (`2d6072e`, `d835a86`). [V]

### Phase A4: improvement study (branch `agent/claude-ml-a4`)

* **Purpose.** Address v1's weaknesses (TRANS, UX, code-switching, small test set) with more data and a transformer, under strict holdout discipline.
* **Implemented, in order:**
  1. Baseline tag; cleanlab scan.
  2. **Holdout frozen first** (`e3ccd24`).
  3. Guide v1.1.
  4. Coder-B pilot: Fable replaced Haiku.
  5. Holdout and 4,000-item expansion labelled (Sonnet + Fable + Opus).
  6. v1 re-review: 32 labels changed; test untouched.
  7. 300 synthetic items generated and blind-verified.
  8. **Protocol pre-registered** (`e541832`).
  9. Candidates E0–E5: 14 runs, including 10 MARBERT runs on MPS.
  10. **Selection committed** (`2b15bc4`).
  11. **Holdout evaluated once** (`1d3cbfa`).
  12. Reports (renderer by Codex); export checksums and pinned inference requirements.
* **Results** (A4 holdout, n = 1,231): selected E4 e2e **0.690**, against v1 **0.489**; paired Δ CI [0.139, 0.260]. E3 scored 0.704 but was not selected: there was no post-hoc switch.
* **Problems → resolutions** [R]:
  1. The Fable usage-limit interruption was handled by auto-restart.
  2. The owner paused before MARBERT. The grid was stopped before its first epoch, with no partial results used, and resumed later.
  3. MPS non-determinism (0.6996 vs 0.6918 for the same configuration and seed) is disclosed, and seeds are averaged.
  4. With only about 11–12 GB of free disk, models were exported in fp16 (max |ΔP| 2e-4).
  5. E0's validation contamination (198/815) means E0 is compared only on the holdout.
* **Status.** **Complete** (`aa4b394`). [V]

### Phase A4-Integration (`integration/a4-marbert`, `integration/a4-environment`)

* **Implemented** [R]:
  * A4 export copied, with SHA256SUMS 6/6 matching.
  * A separate A4 Python environment.
  * `.env` selection of `ML_ARTIFACT_DIR`, version-paired model card, launcher readiness gate and optional ports.
  * 14 A4 acceptance tests.
  * Explicit restart-based rollback to v1 and back.
* **Verified** [R]:
  * 111 Python tests (64 app + 47 ML) and 18 frontend tests passed; build passed.
  * Native-Chrome A4 flows.
  * CSV 4 accepted + 1 invalid, then 4 duplicates on reimport.
  * Dashboard matched SQL; live rollback.
  * Offline probe: 4.99 s cold start, 37.0 ms median request, 1.54 GB RSS.
* **Problems → resolutions** [R]:
  1. A click version conflict: Hugging Face Hub needs click ≥ 8.4.2, but the v1 lock had 8.3.0. Resolved with a separate A4 environment.
  2. Filesystem timeouts during package copies. Resolved by the standalone, hash-locked environment (`9ea34e0`): 60 pinned distributions, audit clean.
  3. A cold-start proxy race. The launcher now waits for backend diagnostics.
  4. An optional re-run in the old environment stalled. It was interrupted and **not counted as passed**.
* **Status.** **Complete; this is the latest fully verified integrated baseline** (`3b2c2cf`). [V/R]

### Phase P1-ML: text + screenshot analysis and system identification (branch `agent/claude-ml-p1`)

* **Implemented:**
  * OCR adapters (Vision, EasyOCR, Tesseract, Paddle).
  * A synthetic OCR set of 64 images, with runner and scorer.
  * A 30-system registry, frozen before evaluation (`a3035f4`), and a rule matcher.
  * The `analyze()` pipeline: OCR, correction, combined text, frozen `predict_text`, systems, error-cue signals.
  * AI-assisted mention labels on 339 reviews.
  * Pipeline and scenario evaluations.
  * 108 P1 tests written by Codex.
* **Results:**
  * Vision CER 0.0021 on synthetic screens.
  * Rules: P 0.958, R 0.628.
  * Pipeline p50 134 ms; RSS 1.56 GB.
* **Problems → resolutions:**
  1. PaddleOCR needs numpy 2.3.5, so it got its own `.venv-paddle`.
  2. EasyOCR at the default canvas used 8 GB; the canvas was cut to 1600, giving 6.3 GB.
  3. Tesseract is poor on UI screens (CER 0.346) and is not the default.
  4. In Codex's sandbox, Vision requests fail with `engine_error` (14 test failures), although all 155 pass in a normal session. This is documented with an EasyOCR fallback.
  5. The narrative-marker rule was added after a development-set inspection, so those numbers are development numbers.
* **Status.** **Complete as an ML component** (`d8ffad4`). [V]

### Phase P1-Integration (`integration/p1`)

* **Implemented** [R]:
  * Typed P1 schemas.
  * `/api/ocr/extract` with server-owned 24-hour drafts and `/api/complaints/analyze-p1`.
  * Atomic P1 provenance persistence and OCR-correction audit.
  * Screenshot UI components; source=image filters.
  * A P1 hash-locked environment (77 distributions including EasyOCR).
* **Verified** [R]:
  * Backend: 93 passed.
  * Frontend: 26 passed; build passed.
  * 3 published Absher screenshots run through EasyOCR → MARBERT → SQLite, in process.
* **Not verified** [R]:
  * In the Codex sandbox, the full ML suite gave 141/155 (14 Vision failures).
  * Localhost bind was denied (EPERM) and no browser was available, so there was **no browser-level P1 acceptance**.
* **Status.** **PARTIAL** (`035f3eb`; milestone M10 IN_PROGRESS). [V/R]

### Phase D: documentation

* **Dossiers.** The ML evidence dossier (`af72c54`) and the app implementation evidence (`071716d`, Codex).
* **This audit** (2026-11-07, `agent/claude-docs`).
  * Read-only checks:
    * SHA-256 verification of the A4 export (6/6 OK) and the v1 artifacts.
    * Uniqueness reconciliation of 7,240 real records.
    * Route and test-function inventory.
    * Per-run metric extraction.
  * **Problem → resolution.** `git worktree add` failed twice with `fatal: mmap failed: Operation timed out / canceled` while writing the full tree. A **sparse checkout** containing only `docs/` and the recovery files was used instead. The cause is NOT VERIFIED: it is consistent with the filesystem latency Codex also recorded [I].

---

## 4. Evolution from proposal to implementation

| Proposal element | Implemented as | Type |
|---|---|---|
| Reviews of ≥ 2 Saudi e-gov apps, ≈ 1,200 complaints, dated time window | Licensed AURA corpora: 7,240 real annotated items, 46.8% gov-domain, 2,843 complaints; **no dates** | Deviation (fallback clause invoked) |
| Two human Arabic coders; 20% double-coded; human discussion | Two independent Claude coders on **100%** of items; Claude adjudicator; no human coding | Deviation (owner decision) |
| Classifier on complaint records only | Complaint gate + category; gate, category and e2e metrics | Extension |
| Dummy, TF-IDF + LR, TF-IDF + SVM | Implemented (v1 grid; A4 E1/E2) | As planned |
| Preprocessing ablations incl. stemming / stop words | P0 vs P1 on validation only; P2 not run | Partial |
| K-Means + near-duplicates | Implemented (v1 data) | As planned |
| Optional transformer | MARBERTv2 (A4), with owner approval; plus multilingual-e5 baseline | As planned (optional, done) |
| Error, dialect and app-level bias, cost analysis | Errors and cost done; dialect and app bias **not** done | Partial |
| H5 actionability rubric | **Not done** | Not implemented |
| — | Pre-registered A4 protocol, new frozen holdout, cleanlab re-review, synthetic augmentation | Added |
| — | Web application (React/FastAPI/SQLite), OCR, system registry (P1) | Added (beyond proposal scope) |
| — | Email/EML ingestion | Explicitly out of scope |

---

## 5. Problems and lessons learned (consolidated)

| # | Area | Problem | Resolution / status | Evidence |
|---|---|---|---|---|
| 1 | AI labelling | Coder B wrote a plan, not labels (pilot) | Strict labelling-only prompt; re-run 100/100 valid | `PROGRESS.md` A1.7 [R] |
| 2 | AI labelling | Degenerate batch `main_05` (30 vs 92–124 complaints) | Quarantined; re-coded; re-adjudicated | `reports/agreement.md` [R] |
| 3 | AI labelling | Haiku over-used `unclear` | Guide rules 8–11; Fable replaced Haiku in A4 (κ 0.80 vs 0.70) | [R/F] |
| 4 | AI labelling | Usage-limit interruption (Fable) | Auto-restart; final files from the completed rerun | [R] |
| 5 | Label noise | 239 cleanlab flags | Blind re-review; 32 changes; test labels untouched. Residual risk: model-guided flagging can bias labels | [F/I] |
| 6 | Python packages | pandas 3 Arrow strings / `groupby.apply` column drop | Explicit conversion / loop; byte-identical regeneration | [R] |
| 7 | Calibration | Uncalibrated LR ECE 0.60 | Sigmoid calibration (v1); temperature scaling (A4) | [R/F] |
| 8 | Apple MPS | Non-deterministic training | Three seeds; median-seed export; disclosed | [R] |
| 9 | Disk | ≈ 11–12 GB free | fp16 export | [R] |
| 10 | Leakage | E0 validation contaminated (198/815) | E0 compared only on the new holdout | [V] |
| 11 | Leakage | Duplicates across corpora (29.9% of AURA-Cls) | Cross-corpus group-aware splitting; leakage tests | [F] |
| 12 | Class imbalance | PERF/TRANS/UX rare | Lexicon- and model-guided enrichment; sqrt class weights; synthetic data. **PERF remains small** (n = 14 holdout) | [F] |
| 13 | Training interruption | Owner pause before MARBERT | Grid stopped before epoch 1; no partial results; resumed | [R] |
| 14 | OCR dependencies | PaddleOCR numpy pin conflict | Separate `.venv-paddle`; not in the app | [R] |
| 15 | OCR resources | EasyOCR 6–8 GB RAM, 1.9–3.3 s per image | Canvas 1600; Vision default on macOS | [F] |
| 16 | OCR platform | Vision `engine_error` in the Codex sandbox | EasyOCR fallback in the app; 14 ML tests remain failing there. **Unresolved for host acceptance** | [R] |
| 17 | App environment | pip network blocked; port bind denied; browser host unavailable | Offline wheels; npm launcher; P1 browser acceptance **still blocked** | [R] |
| 18 | App dependencies | click 8.3 vs ≥ 8.4.2 conflict; filesystem timeouts | Separate standalone hash-locked A4 environment | [R] |
| 19 | App frontend | Fonts 403 / duplicate `node_modules 2` | Independent copy; scoped Vitest/Tailwind discovery | [R] |
| 20 | API / inference compatibility | Keep the 6-key contract across v1/A4/P1 | Frozen `predict_text`; P1 wraps it (`p1-analysis-v1`) without changing it | [V] |
| 21 | Model behaviour | v1 misses mixed-language OTP; MARBERT flags resolved past problems | First fixed by A4 (AUTH 0.987, `integration/app/PROGRESS.md` A2); second **unresolved**, reported | [R/F] |
| 22 | Portability | Locks are macOS-arm64/CPython 3.12 only; Vision is macOS-only; 128-token truncation vs 20,000-character inputs | Documented; **unresolved** | [R] |
| 23 | Documentation | `git worktree add` mmap timeouts | Sparse checkout | [V] |

**Lessons [I].**
* **Freeze, then label, then pre-register.** Freezing the evaluation set first, labelling second and pre-registering selection third made the E3-vs-E4 situation reportable without bias.
* **AI coders need validity checks.** Multiple AI coders require output-validity checks (batch-level label rates) and model substitution based on a pilot.
* **Integration evidence is a separate kind of evidence.** Browser, offline and rollback checks must be recorded separately from model metrics, because passing tests are not accuracy.
* **Platform-specific engines need a fallback** and host-level acceptance, or sandbox results will diverge from normal-session results.
