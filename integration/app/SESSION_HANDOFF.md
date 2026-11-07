# P1 integration recovery

## Read first / ownership

Checkout `Project/integration/`, branch `integration/p1`, from stable `integration/a4-environment` commit3b2c2cf. Read the original P1 user requirements, IMPLEMENTATION_PLAN.md, PROGRESS.md, README.md, P1_SETUP.md, P1_INTEGRATION_VERIFICATION.md and Claude's ml/reports/p1_integration_notes.md. Inspect actual code/Git before continuing. App owner only; no ML training/evaluation edits, email/EML or redesign.

Claude P1 d8ffad4 imported by subtree merge afd3bde; tracked ml tree equals that source exactly. Original infer/A4 export/pins unchanged. Source app/ML/P1 worktrees clean and preserved. Unrelated frontend/node_modules 2 symlink retained, not staged/deleted.

## State / active milestone

M10 IN_PROGRESS: implementation, Backend acceptance, frontend tests/build, environment/assets and documentation complete; **normal-host/browser/Vision acceptance BLOCKED**. Last verified checkpoint P1-3. Verified implementation checkpoint:7175581. Subsequent documentation checkpoint records this hash; no full host acceptance claimed.

Real P1 text + screenshot preview/extract/edit/confirm UI, server-owned OCR drafts, full immutable pipeline evidence, OCR correction audit, review/explorer and image source filters are implemented. No raw image persistence. Unknown/ambiguous/multiple mentions preserved without guessing a primary system. Real/default A4, explicit Mock/P0 separation, V1 rollback retained.

## Runtime / startup (cwd integration/)

- Start: `npm --prefix app run start`. Selected app/.env: APP_PYTHON=backend/.venv-p1/bin/python, APP_ML_MODE=real, A4 ML_ARTIFACT_DIR, HF_HUB_OFFLINE=1, ML_OCR_ENGINE=easyocr, ML_EASYOCR_CANVAS=1600. No PYTHONPATH/PYTHONHOME or experimental DATABASE_URL.
- Ports retained: React http://127.0.0.1:15174; FastAPI http://127.0.0.1:18174/docs. Defaults5173/8000.
- Separate Backend after exporting settings: `app/backend/.venv-p1/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 18174`; frontend `npm --prefix app/frontend run dev -- --host 127.0.0.1` with API/WEB port variables exported.
- P1 standalone environment:77 pinned local packages including optional EasyOCR, official hashed locks/manifests. Audit: `app/backend/.venv-p1/bin/python -I app/backend/verify_a4_environment.py --profile p1-easyocr` passed,25 imports,10 V1/A4+2 OCR assets, pip clean. Original A4 export SHA256SUMS6/6 OK. No external site-packages.
- Original .venv-a4-standalone and lock/cache preserved. Optional old-env re-audit stalled while reading pandas source and was interrupted; do not count that as a new passed audit. Its package pins/locations passed the audit's pre-import checks; no dependency replacement attempted. New P1 runtime fully audited and actually runs A4/V1.
- Both servers are stopped/not running from this session. Actual startup loads A4 but localhost bind is denied by this agent sandbox.

## Database / APIs

Default SQLite backend/storage/complaints.sqlite3:9 original Demo complaints,3 original correction rows,0 real,0 P1 records/drafts. Compared to pre-task backup: every old row unchanged. SQLAlchemy adds only p1_analyses / ocr_drafts; no column rewrite or destructive migration. Additive upgrade verified on a backup.

New POST /api/ocr/extract -> draft OCR, then POST /api/complaints/analyze-p1 -> actual ml.analyze -> unchanged six-key prediction -> atomic Complaint/P1Record/optional ocr_text Correction. Existing REST preserved; ComplaintOut adds nullable p1_analysis. Image source filter added. Historical records not reanalyzed. OCR draft expiry24h, upload10MB/40MP, combined text20000, backlog100. Missing/no text does not fabricate a complaint. Errors explicit, no model/engine fallback hidden from users.

## Verification / limits

- Final Backend93/93 passed with actual EasyOCR+MARBERT (64 original+29 P1), including offline, restart, schema, evidence spans, correction/review, dedup/date/demo/error and existing CSV/V1/A4 tests.
- Frontend26/26 passed using default npm test; TypeScript/Vite production build passed. Component tests mock APIs and are not full browser acceptance.
- Full Backend+ML run before the final extra oversized-header case:233 pass14 fail/no skips. ML portion141 pass14 Vision failures=155. Assertions/source tests unchanged. Do not relabel failures as passes/skips.
- Synthetic Arabic PNG/degraded JPEG/no-text/corrupt cases tested. Three official published Absher UI images also passed real APIs and were marked Demo; OCR garbling and one unwanted complaint prediction documented. They are not private field complaint captures or accuracy gold. P1_SCREENSHOT_OBSERVATIONS.json stores provenance/hashes; full images/results are ignored local artifacts.
- No measured real-screenshot accuracy, no holdout rerun, no retraining.

## Blockers / exact next step

1. Uvicorn bind127.0.0.1:18174 fails Errno1 EPERM (shell and Node tool). Native/browser host unavailable; installed headless Chrome cannot launch. No real browser E2E or visual QA claimed.
2. Vision initializes/ar-SA supported but recognition returns engine_error/Vision request failed:None. Fourteen unchanged ML tests explicitly require Vision. EasyOCR actual inference works offline and is explicitly selected locally.

**Next implementation/acceptance step:** in an ordinary supported local terminal outside this sandbox, run `npm --prefix app run start` with a separate verification DATABASE_URL, then execute the browser checklist in P1_INTEGRATION_VERIFICATION.md: real text, screenshot preview/edit/confirm, evidence/model version, review/explorer/dashboard, restart, CSV/reupload dedup, Arabic/English/mobile and V1→A4 restart rollback. Unset ML_OCR_ENGINE and rerun all155 ML tests on a host with working Vision. Record honest field-screenshot observations if available. Commit that acceptance evidence; only then mark M10 DONE.

## Recovery / artifacts

Ignored backend/storage/p1-recovery/ includes stable-a4.env, stable-a4.sqlite3, selected-p1.env, final test/audit logs, migration/preservation evidence and published-screenshot probes. Normal DB settings restored; previous verification archives untouched. P1_SETUP.md documents fresh online/offline setup and asset transfers. Do not source historical PYTHONPATH-based configs.

V1 rollback: remove ML_ARTIFACT_DIR from .env and caller environment and restart same .venv-p1. Re-add A4/restart to return. Exact pre-P1 application rollback: clean checkout integration/a4-environment and original standalone A4 settings. Preserve both weights and all stored results; no downgrade/drop required for extra tables.
