# Full Stack Application Implementation Plan

Authoritative scope: `../CODEX_APP_DASHBOARD_PLAN.md`, superseded by the user's mandatory React/FastAPI stack and six-page requirements. Owner: Codex; changes are confined to `app/`. No ML training, changes to `ml/`, Streamlit, cloud services, OCR, EML, or clustering in P0.

Task states: **TODO**, **IN_PROGRESS**, **DONE**, **BLOCKED**. DONE requires implementation evidence and verification; a source file alone is insufficient.

## Architecture

- React + TypeScript + Vite + Tailwind CSS; React Router, TanStack Query, Recharts, Lucide React; local Arabic font.
- FastAPI + Pydantic + SQLAlchemy; SQLite initially; portable models and `DATABASE_URL` for future PostgreSQL.
- One local backend and one Vite server with `/api` proxy. No microservices, authentication, Docker, job queues, or ORM abstractions beyond the required SQLAlchemy.
- Backend-owned Mock/Real mode; lazy Real adapter invokes the unchanged `ml.infer.predict_text(text) -> dict` contract. Frontend consumes only REST, so pages do not change when switching predictors.
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
- Real adapter acceptance with actual Claude artifacts is TODO / external dependency, not a blocker for Mock P0.
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
