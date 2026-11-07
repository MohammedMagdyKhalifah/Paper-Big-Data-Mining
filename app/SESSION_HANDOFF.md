# Session Handoff

## Recovery protocol

Read `../CODEX_APP_DASHBOARD_PLAN.md` and the user's mandatory React/FastAPI override, then IMPLEMENTATION_PLAN.md, PROGRESS.md and this file. Inspect source and `git -C app status` before trusting task statuses. All source/config/docs changes stay in `app/`; never modify Claude's `../ml/`.

## Current implementation state

**P0 and M5 bilingual UI/analytics refinement implemented and verified.** React/TypeScript/Vite/Tailwind frontend with Router, TanStack Query, Recharts and Lucide; FastAPI/Pydantic/SQLAlchemy backend with SQLite. No Streamlit. Six pages and all nine requested endpoints exist. Human corrections retain original predictions. CSV ingestion is persistent and deduplicated. Demo and real data are separated.

Active milestone: **M5 complete and delivered locally**.
Last completed milestone: **M5 bilingual design, analytics and verification**.

Latest M5 automated verification: **37 Pytest cases pass; 12 Vitest cases pass; final production TypeScript/Vite build passes**. See PROGRESS.md for browser evidence and prior failures/fixes.

Git: independent repository under `app/`, branch `agent/codex-app`. Initial P0 commit: `ee28839`; inspect latest Git log for the subsequent M5 bilingual/design checkpoint. No remote push/merge performed. Inspect actual Git state on recovery.

## Startup and tests

Commands from the project root (the directory containing app and ml):

```bash
# Dependencies only if needed
python3 -m venv app/backend/.venv
app/backend/.venv/bin/python -m pip install -r app/backend/requirements.lock
npm --prefix app/frontend ci

# Run both services (Ctrl+C stops both)
npm --prefix app run start

# Tests and production build
app/backend/.venv/bin/python -m pytest app/backend/tests -q
npm --prefix app/frontend test
npm --prefix app/frontend run build
```

URLs: frontend http://127.0.0.1:5173 ; backend http://127.0.0.1:8000 ; API docs http://127.0.0.1:8000/docs . Owned preview servers are stopped at final teardown; latest verification tool session was 29815. Restart using the command above; verify ports before reuse.

Separate backend startup: `app/backend/.venv/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000`.
Separate frontend startup: `npm --prefix app/frontend run dev -- --host 127.0.0.1`.

## Database and migration status

SQLite: `app/backend/storage/complaints.sqlite3`. Initial schema, non-destructive create_all; no migrations or database reset. Tests use temporary databases and scoped cache. Current local database holds **9 Demo messages / 8 complaints / 8 pending reviews**. One Demo record has human-corrected category/system with original values preserved. Database and dependency/cache files are ignored; fresh checkout starts empty.

`DATABASE_URL` is configurable and ORM/query design avoids SQLite-specific aggregation; PostgreSQL migration is **not implemented/tested**.

## API and ML status

All requested routes implemented with explicit OpenAPI responses. Default API scope is real; Mock UI explicitly selects demo. `APP_ML_MODE=mock` is default and never imports ml. All Mock scores null. Explicit synthetic-input flags and reserved DEMO- source IDs force demo even under Real.

Real adapter uses unchanged `ml.infer.predict_text` and validates all six fields. Actual Claude model **not verified**; only injected contract/error tests were run. No ML data, artifacts or training code modified. No fake evaluation results. Optional readonly evaluation report is shown only for a configured version matching a successful Real call. README/INTEGRATION_NOTES document the setup.

## Known limits and next step

No known unresolved P0 defect from executed checks. PII masking is limited to documented patterns. CSV max 10MB/5,000 rows; text max 20,000 chars. No auth, cloud, OCR, EML, clustering, system-name inference or training.

**Exact next task:** await user feedback on the completed bilingual design, or verify the actual Real model once Claude confirms artifact/dependency readiness. M5 browser QA is complete (desktop and mobile 390×844, Arabic and English). Language is stored as marsad.language; complaint/model content stays Arabic. Additive overview metrics include no_review_required_messages, known_system_complaints, dated_complaints, sources, and optional previous-period comparison. No DB migration or ML contract change.

Native Chrome through cua_repl was used because the browser connector host was unavailable. After compaction, call cua.rewriteDocumentation() before continuing any UI task. Read README for operational commands and PROGRESS for verification history.
