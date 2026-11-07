# Full Stack Application Implementation Plan

Authoritative scope: `../../CODEX_APP_DASHBOARD_PLAN.md` (original project copy), superseded by the user's mandatory React/FastAPI stack and six-page requirements. Owner: Codex; changes are confined to `app/`. No ML training, changes to `ml/`, Streamlit, cloud services, OCR, EML, or clustering in P0.

Task states: **TODO**, **IN_PROGRESS**, **DONE**, **BLOCKED**. DONE requires implementation evidence and verification; a source file alone is insufficient.

## Architecture

- React + TypeScript + Vite + Tailwind CSS; React Router, TanStack Query, Recharts, Lucide React; local Arabic font.
- FastAPI + Pydantic + SQLAlchemy; SQLite initially; portable models and `DATABASE_URL` for future PostgreSQL.
- One local backend and one Vite server with `/api` proxy. No microservices, authentication, Docker, job queues, or ORM abstractions beyond the required SQLAlchemy.
- Backend-owned Mock/Real mode; Real defaults on with non-persisting startup loading and invokes the unchanged `ml.infer.predict_text(text) -> dict` contract. Frontend consumes only REST, so pages do not change when switching predictors.
- Immutable original prediction plus effective current fields; append-only corrections; real/demo separation; deduplicated imports; distinct original and import timestamps.

## P0 milestones

### M0 Setup and isolation — DONE

- DONE: Read the full source instructions and reconcile the mandatory web stack.
- DONE: Inspect existing source; no previous `app/` implementation existed.
- DONE: Initialize independent Git repository on `agent/codex-app` within `app/` (user-approved alternative to root worktree).
- DONE: Establish Python virtualenv, frontend dependencies, local ignores, and two-service development launcher.
- DONE: Install dependencies and verify backend imports and initial Vite build.
- Acceptance evidence: independent Git state, successful Python imports, successful frontend build. See PROGRESS.

### M1 Database and predictor boundary — DONE

- DONE: SQLAlchemy Complaint and Correction tables, foreign keys, unique fingerprint, noncomplaint/category constraint.
- DONE: Original prediction and original system preserved; effective fields separately editable.
- DONE: Mock examples covering six categories and noncomplaint; all Mock records marked demo and scores null.
- DONE: Strict six-field prediction validation and lazy Real import; explicit failures without Mock fallback.
- DONE: UTC timestamps with Riyadh interpretation/display; no invented event timestamp.
- Acceptance evidence: Pytest tests for adapter, persistence, redaction, corrections, and timestamp behavior.

### M2 REST ingestion, review, analytics — DONE

- DONE: POST `/api/complaints/analyze`.
- DONE: POST `/api/complaints/import` (UTF-8/BOM CSV, row-level failures, limits, deduplication).
- DONE: GET `/api/complaints` (filters, literal text search, pagination).
- DONE: GET `/api/complaints/{id}`.
- DONE: PATCH `/api/complaints/{id}/review` (atomic effective changes and correction log).
- DONE: GET `/api/dashboard/overview` and `/api/dashboard/trends`.
- DONE: GET `/api/systems`.
- DONE: GET `/api/models/info` (no fabricated evaluation; local report only when associated with a successfully observed real model version).
- DONE: Count verification against independent SQL; error handling; partial import on model failure.
- Acceptance evidence: 29 passing backend cases; tests will be extended if fixes change behavior.

### M3 Arabic React interface — DONE

- DONE: Dashboard with KPIs, issue distribution, system ranking and dated trends.
- DONE: Analyze text and CSV import with persisted results and row report.
- DONE: Complaints Explorer with search, filters, pagination and detail/review panel.
- DONE: Systems Analytics with per-system categories and shares.
- DONE: Review Queue with immutable original view and human corrections.
- DONE: Model Information with honest integration/evaluation status.
- DONE: Source implemented for all six pages; initial TypeScript/Vite build succeeds.
- DONE: Fixed the frontend mutation wrapper; all 8 frontend tests pass and page flows verified.
- DONE: Verified browser rendering and end-to-end flow on desktop and mobile 390×844.
- Acceptance: responsive RTL pages, persistent mode banner, loading/empty/error states, API-backed interactions, accessible form labels, no fabricated metrics.

### M4 Integration and release checks — DONE

- DONE: Backend Pytest suite (34 passing in final verification).
- DONE: Vitest component suite (8/8 passing in final verification).
- DONE: Initial TypeScript and production build.
- DONE: Both local servers launched via `npm run start` from `app/`.
- DONE: Verified HTTP readiness and native Chrome import, analyze, review/explorer component, correction, counts and navigation.
- DONE: Final affected suites pass: 34 backend tests, 8 frontend tests; production build passes.
- DONE: Added typed analytics/model responses and verified their OpenAPI schemas.
- DONE: README and integration notes include exact commands, contracts and verification limits.
- DONE: Source inventory and Git inspection completed; persistent final handoff prepared.
- Acceptance: backend tests + frontend tests + production build pass; local service flow verified; no writes outside app; remaining Real-model acceptance stated honestly.

## Dependencies and deferred work

- M3 uses stable M2 REST responses; no dependency on Claude finishing training.
- DONE: actual Claude artifact acceptance completed in M6; Mock remains independently testable.
- PostgreSQL migration/data transfer is deferred; portable model design does not claim a tested migration.
- P1 requires user approval after P0: OCR, EML, explicit system-name matching. No automatic expansion.

## Recovery protocol

Read original requirements, this plan, PROGRESS.md, SESSION_HANDOFF.md; inspect actual source and `git -C app status`; verify documentation against tests and implementation; resume the first incomplete task. Never overwrite earlier progress or infer success from written code.

## M5 Bilingual interface and analytics refinement — DONE

- DONE: Persisted Arabic/English UI language with correct RTL/LTR; complaint text, system names and ML category content stay Arabic.
- DONE: Refresh the visual shell, dashboard, filters, cards and responsive layouts.
- DONE: Add additive overview metrics for effective no-further-review status, system/date coverage, source mix and equal-length prior-period comparison when both date bounds exist.
- DONE: Interactive category/system drilldowns and systems/category matrix using existing APIs.
- DONE: Localized forms, explorer, review and model information; retain backend/model messages and content without translation APIs.
- DONE: Backend analytics correctness tests; frontend language persistence/direction/content preservation and interaction tests; build and desktop/mobile browser QA.
- DONE: Update README, progress and session handoff with verified results.

## M6 Real ML integration and end-to-end verification — DONE

User authorized integration of application commit e034f9b and Claude ML commit a02d2fa. Original agent checkouts/branches must remain unchanged.

- DONE: Inspect both Git histories, clean states and worktree lists.
- DONE: Create isolated `integration/` repository, branch `integration/real-ml`; import both histories as unsquashed subtrees at app/ and ml/. Imported trees match source commit tree hashes exactly.
- DONE: Copy ignored local weights with matching SHA-256 and preserve original SQLite via backup copy.
- DONE: Assemble a compatible local backend/inference environment without modifying source environments or retraining; exact runtime and optional ML-test pins validated.
- DONE: Make Real the default, perform non-persisting startup load, keep explicit Mock mode and no silent fallback; preserve six-field predictor contract.
- DONE: Actual-model API/schema/persistence/offline/error tests; 50 Backend + 20 unchanged ML tests pass without skips; 15 frontend tests and production build pass.
- DONE: React → FastAPI → Real ML → SQLite → React browser verification, including mixed/noncomplaint/empty/unknown/CSV/date cases, real AURA import/reimport, review and restart.
- DONE: Operation/integration docs and recovery record updated; verification database archived, default restored, and verified integration committed as 2d6072e. No push or agent-branch reset.

M6 evidence: INTEGRATION_VERIFICATION.md, MODEL_ASSETS.json and Integration checkpoints I1–I3. Source ML branch independently advanced to ignore-only commit 80511e7 while this integration was running; A4 worktree was left untouched. This integration intentionally retains the requested a02d2fa snapshot.

## M7 English digits throughout the UI — DONE

- DONE: Shared counts, percentages, IDs, scores and timestamps use English digits 0–9 in Arabic and English browsing. Preserve Arabic labels/content, RTL/LTR, Gregorian calendar and Riyadh time.
- DONE: Regression coverage for both languages and date/time formatting; 17 frontend tests pass, TypeScript/Vite production build passes.
- DONE: Limit Vitest and Tailwind discovery to application source so the pre-existing untracked duplicate dependency symlink does not supply tests or delay builds. Keep that unrelated local path untouched; generated production CSS is unchanged.
- DONE: README, append-only progress and recovery record updated. Backend/database/ML unchanged.

## M8 A4 MARBERTv2 integration — DONE

- DONE: Read A4 handoff, inspect actual repositories/worktrees, create integration/a4-marbert from verified d835a86; merge exact Claude aa4b394 through existing ml subtree, preserving integration/real-ml and source branches.
- DONE: Verify all six export SHA256SUMS entries including ignored safetensors; preserve V1 artifacts/environment. Compatible A4 interpreter verified with explicit read-only local package references; standalone installation limitation documented.
- DONE: Configure A4 opt-in through ML_ARTIFACT_DIR, offline startup/cache/error behavior, explicit live V1 rollback by removing setting; launcher waits for Backend readiness before Vite.
- DONE: Match actual A4 source model card to active known bundle/version; preserve every API schema and separate dataset labels. No holdout rerun.
- DONE: 111 Python tests (64 Backend + all 47 unchanged ML), 18 frontend tests, production build; native Chrome full flow/review/restart and actual service rollback. Cold offline startup 4.9879s, median Analyze+SQLite 37.0013ms. Optional old standalone V1 env collection stalled; explicitly not counted as passing.
- DONE: README, verification/progress/handoff and final checksum/history/schema checks complete; verified integration committed as 03a006f. No redesign, training changes or push.

## M9 Self-contained reproducible A4 environment — DONE

- DONE: Preserve verified A4 branch/config and V1 rollback; create integration/a4-environment from 01f0b43 and back up local settings.
- DONE: Fresh project-local .venv-a4-standalone installed from 60 fully pinned/hash-verified official wheels; transitive target lock and manifest added; original environments preserved.
- DONE: Isolated and normal audits prove local-only imports, no Python path overrides/system/user packages; 10 receipt assets and original 6-entry A4 SHA256SUMS match. Network/external-package reads blocked during real A4→V1→A4 execution.
- DONE: 111 Python tests (64 Backend + all 47 unchanged ML), 18 frontend tests and production build pass in new environment; actual two-service startup/HTML/API proxy verified, normal DB unchanged.
- DONE: Switched active config after acceptance, removed Python path override; fresh online/offline setup, audit/verification and recovery documented. Final preservation checks passed, previews stopped, verified implementation committed as 9ea34e0. No blocker or P1/features/model changes.

## M10 P1 text / screenshot integration — IN_PROGRESS

Authorized scope: local text, PNG/JPEG OCR, human OCR correction and evidence-based system mentions only. No email/EML, training, holdout reruns or redesign.

- DONE: Inspect stable A4, original worktrees, P1 docs/interfaces/tests; preserve source branches and stable environment. Dedicated integration/p1 from 3b2c2cf; exact Claude d8ffad4 subtree merged. A4 export/infer/pins unchanged. Local settings and SQLite backed up.
- DONE: New isolated P1 runtime from existing complete A4 lock plus pinned Pillow/Apple Vision packages; keep .venv-a4-standalone untouched. Hash-lock dependencies, verify assets and real engine support.
- DONE: Backend additive OCR draft/provenance tables and typed endpoints: POST /api/ocr/extract and POST /api/complaints/analyze-p1. Server-owned OCR result, upload/decode/text limits, expiry and explicit errors. Preserve old REST and six-field inference contracts.
- DONE: Invoke actual ml.analyze pipeline; persist immutable P1 evidence, corrected OCR text, original OCR text and effective review fields atomically. Preserve unknown/ambiguous/multiple systems without guessing one.
- DONE: Extend existing bilingual Analyze page with upload/preview/extract/edit/confirm flow and evidence panel, reused in Explorer. No redesign. Preserve English digits and real/demo separation.
- DONE: Meaningful API/schema/error/persistence/dedup/review tests and frontend interactions: 93 Backend, 26 Vitest and build pass. Real EasyOCR/MARBERT, offline, restart and existing V1/A4 rollback verified. Full ML run:141 pass14 fail due to actual Vision sandbox denial; not counted as fully passed.
- DONE: Synthetic and3 official published UI screenshot API probes; provenance/hashes and undesirable/noisy outputs documented without accuracy claims. These are not private field complaint captures.
- BLOCKED: Actual localhost/browser workflow and normal-host Vision/14 ML cases: sandbox denies bind (EPERM), Vision request fails, browser/native host unavailable. Exact recovery acceptance steps in P1_INTEGRATION_VERIFICATION.md. Real Arabic field captures remain an explicit coverage limitation.
- DONE: Fresh setup, contracts, verified results, limitations and recovery documentation.
- DONE: Verified implementation checkpoint committed as7175581; full acceptance remains pending host verification. M10 stays IN_PROGRESS with its two explicit host gates BLOCKED.

Dependencies: M9 stable A4; Claude P1 d8ffad4; supported local OCR engine. Acceptance: browser → FastAPI → actual OCR → user correction → unchanged MARBERT → system evidence → SQLite → React, with explicit errors, no guessed names and stable A4/V1 recovery.
