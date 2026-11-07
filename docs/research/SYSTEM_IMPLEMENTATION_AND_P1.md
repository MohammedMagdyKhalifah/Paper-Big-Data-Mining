# System Implementation and P1

**Project:** *Beyond Sentiment: Mining Actionable Service Failures from Arabic Digital Service Complaints Using Machine Learning*

**Document role:** this document covers three things:
* the P1 OCR and system-identification component (ML side);
* the full-stack application (Codex);
* their integration status.

It **distinguishes completion of the ML component from verified integration into React/FastAPI.**
* Scientific model metrics: `ALL_EXPERIMENTAL_RESULTS.md`.
* History: `COMPLETE_PROJECT_HISTORY.md`.

**Conventions**
* **Paths.** Unprefixed paths are relative to the ML repository root (branch `agent/claude-ml-p1`). `integration/` means `Project/integration/` (branch `integration/p1`, source cutoff `035f3eb`, documentation commit `071716d`).
* **Evidence tags.**
  * **[V]**: verified in this audit (2026-11-07).
  * **[F]**: from a cited result file.
  * **[R]**: reported in a Codex or Claude verification record, not re-executed in this audit.
  * **[I]**: interpretation.
* **No tests were rerun** and no application server was started for this audit.

**Scope exclusions.** E-mail ingestion, mailboxes and EML processing are **not implemented and out of scope** (`reports/p1_integration_notes.md` §7; `integration/app/P1_INTEGRATION_VERIFICATION.md`). OCR training and NER fine-tuning are also out of scope.

---

## Part A: P1 ML component (branch `agent/claude-ml-p1`, commits `a3035f4`, `977f496`, `d8ffad4`)

### A.1 Interface (`analyze.py`; `reports/p1_integration_notes.md`)

* `ml.infer.predict_text(text)` is **unchanged**: 6 keys, trained model only.
* P1 adds three functions around it:
  * `analyze(text=None, image=None, *, image_ocr=None, corrected_text=None, ocr_engine=None)` returns schema `p1-analysis-v1`.
  * `extract_text(image, *, engine=None)` performs OCR only, for the two-step correction flow.
  * `find_systems(text)` performs system detection only.
* **Result keys:**
  * `schema_version`.
  * `analysis_kind`, one of: complaint · not_complaint · error_screen_signal · no_text · ocr_failed.
  * `input`, with `text_source` and `classified_text`.
  * `prediction`: the exact `predict_text` output, or null.
  * `systems`, with status identified / ambiguous / unknown, `systems[]`, `possible_mentions[]`, `generic_references[]`, `registry_version` and `method`.
  * `signals`, with error-message cues, narrative markers, `needs_user_context` and `ocr_needs_review`.
  * `ocr`, with status ok / empty / failed, lines with confidences, error codes, engine and image metadata.
  * `notes`.
  * `timing_ms`.
* **Spans.** Every span indexes into `classified_text`. [F]

### A.2 Text and image workflow

1. **Typed text** is classified directly.
2. **Images** must be PNG or JPEG, ≤ 40 MP. They go to `extract_text`.
   * A bad image never raises an exception. It returns `ocr.status = "failed"` with a code: `unsupported_format`, `unreadable_image`, `file_not_found` or `engine_error`.
3. **Correction flow.** The UI shows the OCR text, with a warning when confidence is low. The user may correct it. Corrected text replaces the OCR text for classification.
4. **Combined input.** `classified_text` = user text + newline + image text. It goes to the frozen `predict_text`, and then to `find_systems`.
5. **`error_screen_signal`** is raised for image-only input that contains an error cue and no first-person or narrative marker (`configs/error_cues.yaml`). The model prediction is still attached. The signal **asks for context; it is not a diagnosis**.

### A.3 OCR engines: synthetic benchmark only

**Evaluation set** (`scripts/p1_make_ocr_eval.py`, seed 31):
* 32 screens, each as a clean PNG (1000×2000) and a degraded JPEG (×0.6, q55): **64 images, 60 with text**.
* Content: 12 hand-written Arabic error screens, 6 chats, 12 real AURA review texts and 2 no-text screens.
* Rendering: headless Chrome on macOS, SF Arabic / Geeza Pro / Arial fonts, light and dark themes.
* Reference: the exact DOM text.
* **Synthetic images only**: `data/ocr_eval/real/` does not exist (only `data/ocr_eval/synthetic/`; checked 2026-11-07 [V]). [F]

| Engine | Version / setting | CER light | WER light | CER letters | No-text → empty | Text images ok / empty | p50 | Peak RSS |
|---|---|---|---|---|---|---|---|---|
| **Apple Vision** | macOS 27.0.1; ar-SA + en-US; accurate | **0.0021** | **0.0163** | 0.0004 | 4/4 | 60 / 0 | 124.2 ms | 321 MB |
| EasyOCR | 1.7.2, canvas 1600 | 0.0338 | 0.1508 | 0.0199 | 4/4 | 60 / 0 | 1,864.7 ms | 6,348 MB |
| EasyOCR | 1.7.2, default canvas 2560 | 0.0351 | 0.1508 | 0.0215 | 4/4 | 60 / 0 | 3,315.2 ms | 8,099 MB |
| PaddleOCR | 3.7.0, PP-OCRv5 arabic | 0.0482 | 0.1247 | 0.0352 | 4/4 | 60 / 0 | 8,614.8 ms | 12,607 MB |
| Tesseract | 5.5.2, tessdata_best ara+eng | 0.3458 | 0.3623 | 0.3435 | 0/4 | 51 / 9 | 276.9 ms | 192 MB (+159 MB child) |

Source: `results/p1/ocr_metrics_synthetic.json` [F].
* **Normalisation.** "Light" = NFKC, digit folding, no diacritics or tatweel, collapsed whitespace. "Letters" additionally folds alif/ya/ta-marbuta and drops punctuation.
* **Tuning.** No engine was tuned for accuracy. One generic rule drops lines that contain no letter or digit.
* **Bias toward Vision** [I]. The fonts are Apple system fonts rendered on macOS, so the set plausibly favours Vision. Android screenshots, camera photos and busy backgrounds are not represented. **No real-world OCR accuracy may be claimed.**
* **Vision limitations.** macOS only; the model version follows the OS; line confidences are coarse (0.3 / 0.5 / 1.0) and uncalibrated.
* **OCR correction** is a user action. There is no automatic OCR post-correction model.

### A.4 OCR → classification robustness (`results/p1/pipeline_eval.json`) [F]

* **Agreement.** `predict_text(reference text)` and `analyze(image)` (Vision + `a4-marbert-v1`) agreed on is_complaint, category and needs_review for **100%** of 30 clean and 30 degraded images.
* **Score drift.** Max |Δ complaint_score| was 0.0005 (clean) and 0.0008 (degraded).
* **Scope.** This measures robustness to OCR noise on synthetic screens. It is not a measure of accuracy.
* **Error-screen rule, development set:**
  * Error screens 24/24 → signal; chats 12/12 → complaint; reviews 16 complaint / 6 not / 2 signal; no-text 4/4.
  * The narrative rule was added after inspecting this set.
* **Error-screen rule on 2,000 real AURA reviews:** 32 contain a cue, 20 of which would be flagged. False-flag rate 0.010 overall, **0.625 among cue-containing texts**.

### A.5 System registry and identification (`configs/systems.yaml`, `src/systems.py`)

* **Registry.** A YAML list of **30 Saudi government/public digital services**, each with `aliases`, `ambiguous` names and `exclude_after` idioms.
  * Registry v1 was frozen in `a3035f4` **before** the evaluation sample was drawn.
  * v1.1 added aliases after evaluation; its scores are in-sample.
* **Method.** Transparent rules: **no learned model, no NER**.
  * **Explicit mention.** A registered alias (multi-word names, Latin spellings) identifies the system directly.
  * **Ambiguous names that are ordinary words** (ابشر "sure", صحتي "my health", موعد "appointment") are identified only with a context cue in the 3 preceding tokens, or when quoted. Otherwise they are returned as `possible_mentions`: shown for user confirmation, **not identified**.
  * `exclude_after` removes idioms such as توكلنا على الله.
  * Generic references (التطبيق "the app") are reported separately.
* **Meaning.** Identification means "the text names this system", **not** "this system failed".

**Evaluation** (seed 2031; 339 deduplicated AURA reviews):
* Strata: 239 name-hit items (≤ 12 per system) and 100 gov-app no-hit items.
* **Labels.** AI-assisted, blind Sonnet + Fable: 334/339 item agreement, pair κ 0.9821. 5 items were Opus-adjudicated and 13 flagged uncertain. The reference contains 145 (item, system) pairs over 125 items. [F]

| Method | TP | FP | FN | Precision | Recall | F1 | Item exact match |
|---|---|---|---|---|---|---|---|
| **Rules v1 (shipped)** | 91 | 4 | 54 | **0.9579** | 0.6276 | 0.7583 | 0.8496 |
| Ablation: ambiguous names without context | 137 | 50 | 8 | 0.7326 | 0.9448 | 0.8253 | 0.8319 |
| Naive substring | 144 | 138 | 1 | 0.5106 | 0.9931 | 0.6745 | 0.6077 |
| Rules v1.1 (**in-sample, optimistic**) | 94 | 4 | 51 | 0.9592 | 0.6483 | 0.7737 | 0.8584 |

**Error analysis** [F]:
* **Possible mentions.** 92 ambiguous names were returned as possible mentions; 46 are true mentions. Identified plus possible together cover 137/145 reference pairs.
* **False positives.** "تطبيق وطني", the slogan "كلنا امن وامان", "سبل الراحة" (matched SPL) and "تطبيقات بلدي".
* **Misses.** Unregistered variants such as النفاذ، النفاذ الموحد، بوابة النفاذ، تطمنا، عالنفاذ.

**Not evaluated:** screenshots, as opposed to review text; non-government services (telecom, banking, delivery); population-rate precision and recall (the sample is enriched).

### A.6 Pipeline cost (`results/p1/pipeline_eval.json`; M2 Max CPU; one process with Vision + MARBERT) [F]

| Measure | Value |
|---|---|
| Warm-up | 3.83 s warm cache; ≈ 19 s cold |
| OCR per screenshot | p50 103.6 ms, p95 118.0 ms |
| Classification | p50 31.8 ms, p95 39.7 ms |
| System matching | p50 0.23 ms |
| Total per screenshot | p50 134.1 ms, p95 152.9 ms |
| Peak RSS | 1,555.6 MB |

With EasyOCR instead of Vision, add 1.9–3.3 s per image and 5–7 GB of peak memory.

### A.7 P1 ML tests and status

* **Tests.** `tests/test_p1_{ocr,systems,analyze}.py` (written by Codex; 108 tests).
* **Full ML suite, normal session.** **155 passed**, reported 2026-10-31 and re-run while preparing `reports/ACADEMIC_ML_EVIDENCE.md`. [R]
* **Codex sandbox.** Vision requests failed with `engine_error`, giving 14 failures. [R]
* **Status.** The ML component is **COMPLETE**. Real-screenshot accuracy is **NOT VERIFIED**.

---

## Part B: full-stack application (Codex; `integration/app/`)

### B.1 Technology stack (locked versions from `integration/app/frontend/package-lock.json` and the backend lock files) [R, cross-checked against `integration/app/ACADEMIC_IMPLEMENTATION_EVIDENCE.md` §2]

| Layer | Technology |
|---|---|
| Frontend | React 19.3.1, TypeScript 5.9.3, Vite 8.3.5, Tailwind CSS 4.3.3, React Router 7.18.5, TanStack Query 5.105.0, Recharts 3.10.1 |
| Backend | FastAPI 0.121.2, Uvicorn 0.38.0, Pydantic 2.12.4, SQLAlchemy 2.0.44, SQLite |
| Inference | PyTorch 2.15.0, Transformers 5.22.0, Tokenizers 0.23.3, Safetensors 0.8.0; scikit-learn 1.9.1 for v1 |
| OCR | Pillow 13.0.0; PyObjC 13.0 (Vision); optional EasyOCR 1.7.2 |
| Tests | Pytest 9.2.0; Vitest 5.0.5 + jsdom |
| Toolchain | CPython 3.12.7, Node 22.20.0, npm 10.9.3 |

* **Backend v1 requirements.** `integration/app/backend/requirements.txt` pins `fastapi==0.121.2`, `uvicorn==0.38.0`, `SQLAlchemy==2.0.44` and `pydantic==2.12.4`. [V]
* **Page modules.** `Analyze`, `Dashboard`, `Explorer`, `Model` and `Systems` exist in `integration/app/frontend/src/pages/`. [V]
* **Routes.** `/`, `/analyze`, `/complaints`, `/review`, `/systems` and `/model` are declared in `frontend/src/App.tsx`. [V]

### B.2 REST endpoints (present in `integration/app/backend/main.py`, lines 61–149) [V]

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/complaints/analyze` | Legacy text analysis via `RealPredictor` → `ml.infer.predict_text` |
| POST | `/api/ocr/extract` | Upload PNG/JPEG → local OCR → redacted, server-owned draft (24 h; no complaint inserted) |
| POST | `/api/complaints/analyze-p1` | Text and/or draft id + optional correction → `ml.analyze` → persisted complaint + P1 provenance |
| POST | `/api/complaints/import` | CSV import (≤ 10 MiB, ≤ 5,000 rows); per-row report |
| GET | `/api/complaints` | List/search/filter/paginate |
| GET | `/api/complaints/{id}` | Detail incl. original prediction and correction history |
| PATCH | `/api/complaints/{id}/review` | Human correction of effective fields, with audit rows |
| GET | `/api/dashboard/overview` | Stored-record aggregates |
| GET | `/api/dashboard/trends` | Time buckets by original-event or import time; missing-date count |
| GET | `/api/systems` | Per-system counts and category mix |
| GET | `/api/models/info` | Active/observed model versions, load status, paired model card |

**Persisted entities** (`integration/app/backend/database.py`) [R]:
* `complaints`: current and original prediction, `model_version`, system fields, fingerprint, `is_demo`.
* `corrections`: field, old and new values, time.
* `p1_analyses`: full P1 result and image SHA-256; image bytes are not stored.
* `ocr_drafts`.

### B.3 Feature status

The status vocabulary is the one requested for this audit:
* **IMPLEMENTED**: present in source.
* **VERIFIED**: a recorded test or real workflow exists ([R], not re-run here).
* **PARTIAL**: some layers are verified and an acceptance step is outstanding.
* **NOT IMPLEMENTED**.
* **NOT ACCESSIBLE**: no inspectable evidence.

| Feature | Status | Evidence / boundary |
|---|---|---|
| React + TypeScript + Vite + Tailwind frontend | **VERIFIED** | Builds and Vitest suites pass at the A4 and P1 checkpoints (`integration/app/ENVIRONMENT_VERIFICATION.md`, `P1_INTEGRATION_VERIFICATION.md`) |
| FastAPI + Pydantic + SQLAlchemy backend | **VERIFIED** | 111 Python tests (A4 standalone); 93 backend tests (P1) |
| SQLite persistence and restart survival | **VERIFIED** | Restart/persistence tests; browser records (A4) |
| REST endpoints (11) | **VERIFIED** | Routes present [V]; API tests [R] |
| Model inference adapter (`RealPredictor`, explicit Mock mode, no silent fallback) | **VERIFIED** | Real-artifact tests compare API output with direct `predict_text` |
| A4 MARBERT in the app | **VERIFIED** | Native-Chrome flow at `01f0b43`; standalone offline audit at `3b2c2cf` |
| Text analysis UI | **VERIFIED** (A4 legacy path) / **PARTIAL** (current P1 path: API + component tests only) | The P1 checkout routes Real-mode text through `/analyze-p1` |
| Screenshot OCR UI (preview, extract, edit, context, confirm) | **PARTIAL** | API tests with real EasyOCR + MARBERT and component tests pass; **no browser acceptance** |
| System-evidence display | **PARTIAL** | API/component tested; browser not verified |
| Dashboard analytics | **VERIFIED** (A4 baseline; dashboard matched SQL) / **PARTIAL** for P1 image-source additions | Aggregates of *stored effective* classifications. Not outage detection or population estimates |
| CSV import with deduplication | **VERIFIED** | Browser: 4 accepted + 1 invalid; reimport 4 duplicates |
| Review and correction with audit trail | **VERIFIED** | Original prediction kept; corrections appended. Corrections do **not** retrain the model |
| Model version tracking (per record) | **VERIFIED** | Mixed A4/v1 records retained with versions |
| Offline execution | **VERIFIED** | Socket-blocked cold-start probe; audit found no external package reads |
| Dependency locking | **VERIFIED** for macOS arm64 / CPython 3.12 only | A4 lock 60 distributions; P1 66 / 77 with EasyOCR; `--require-hashes` |
| Model rollback (A4 → v1 → A4) | **VERIFIED** | Explicit `.env` change + restart; not automatic failover |
| Apple Vision in the app | **PARTIAL / NOT VERIFIED on a normal host** | `engine_error` in the Codex sandbox; EasyOCR fallback used |
| Backend tests | **VERIFIED** | 93 passed (P1 final), 11 warnings |
| Frontend tests | **VERIFIED** | 26 passed (P1); API doubles, not browser-to-model |
| ML tests inside the integrated environment | **PARTIAL** | 141/155 (14 Vision failures in the sandbox). 155/155 in the ML-owned environment [R] |
| Full P1 browser workflow (React → HTTP → OCR → MARBERT → SQLite → React) | **NOT VERIFIED** | localhost bind EPERM; browser host unavailable |
| Application screenshots of the running UI | **NOT ACCESSIBLE** | None saved (`ACADEMIC_IMPLEMENTATION_EVIDENCE.md` §11) |
| Authentication / access control / multi-user deployment | **NOT IMPLEMENTED** | Local prototype only |
| Versioned DB migrations | **NOT IMPLEMENTED** | `create_all`; additive P1 tables |
| E-mail / EML ingestion | **NOT IMPLEMENTED** (out of scope) | — |
| Automatic retraining from corrections | **NOT IMPLEMENTED** | — |
| Load, concurrency or user-study evaluation | **NOT IMPLEMENTED** | — |

### B.4 Recorded application measurements (not load tests) [R]

| Measurement | Value | Boundary |
|---|---|---|
| A4 cold app start (socket-blocked) | 4.988 s | after imports; historical runtime |
| A4 Analyze request | median 37.0 ms, max 39.9 ms (8 serial requests) | TestClient incl. SQLite write; no browser |
| A4 process peak RSS | 1,535,344,640 B | benchmark process |
| Standalone A4 cold start | 6.107 s | separate probe |
| Published Absher screenshots, EasyOCR (canvas 1600) | 4,286 / 4,343 / 10,131 ms | one run each; 392×696, 576×768, 576×768 px |

### B.5 Screenshot probes in the application (qualitative only) [R]

* **Images.** Three developer-published images were taken from the Absher App Store listing. They were marked Demo, and their URLs and hashes are in `integration/app/P1_SCREENSHOT_OBSERVATIONS.json`.
* **Results.**
  * Phone composition: non-complaint, Absher identified from English text.
  * Welcome screen: non-complaint, system unknown, heavy garbling.
  * Services screen: **classified as a complaint** although it is a menu.
* **What was not measured.** No CER, WER or accuracy was computed. These are public product images, not field complaints.

---

## Part C: integration status summary

| Layer | A4 | P1 |
|---|---|---|
| ML component | COMPLETE (`aa4b394`) | COMPLETE (`d8ffad4`) |
| Imported into the app | yes (`e7d8ee1`) | yes (`afd3bde`; tree equals `d8ffad4`) |
| App API tests with the real model | VERIFIED | VERIFIED (EasyOCR fallback) |
| Browser acceptance | VERIFIED (`01f0b43`) | **NOT VERIFIED** |
| Offline / standalone environment | VERIFIED (`3b2c2cf`) | audit VERIFIED (77 distributions); host acceptance pending |
| Normal-host Vision | n/a | **NOT VERIFIED** in the app |

**Remaining acceptance** (`integration/app/P1_INTEGRATION_VERIFICATION.md`):
1. On a normal macOS host, run `npm --prefix app run start` and verify that the ports are reachable.
2. Run all 155 ML tests with Vision.
3. Carry out the real-browser P1 flows: Arabic/mixed text, PNG/JPEG, edit and confirm, review, filters, restart.
4. Test real field screenshots if available.
5. Repeat the rollback check and commit the acceptance checkpoint.

**Corrects an earlier ML-side statement.** `reports/ACADEMIC_ML_EVIDENCE.md` §8.6 said that website integration was "NOT VERIFIED from the ML side". This audit inspected the integration repository directly:
* A4 integration is **VERIFIED**.
* P1 integration is **PARTIAL**.
* The default of `ml.infer` remains `tfidf-baseline-v1`; the application selects A4 through `ML_ARTIFACT_DIR`.
* The same dossier describes `data/ocr_eval/real/` as empty. The directory does not exist; either way, no real screenshots are available.
