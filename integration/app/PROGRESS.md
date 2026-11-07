# Implementation Progress

Append verified milestones; do not replace earlier entries. Scope is `app/` only.

## Checkpoint 1 — Foundation and backend verified

Implemented:
- Independent Git repository, branch `agent/codex-app`, under `app/`.
- FastAPI routes, strict predictor schemas, Mock/Real adapter, SQLAlchemy/SQLite database, CSV ingestion, deduplication, correction audit, filtered analytics.
- Six React page sources, RTL shell, local Arabic font, mode banner, API client, query cache, charts and forms.
- Two-service local launcher (`dev.mjs`).

Main files: backend `main.py`, `schemas.py`, `database.py`, `services/*`, `tests/test_app.py`; frontend `src/App.tsx`, `src/pages/*`, `src/components/common.tsx`, `src/api.ts`, `src/types.ts`, `src/styles.css`, `src/test/*`; dependency manifests and local ignores.

Verified commands/results:
- `app/backend/.venv/bin/python -m pip check`: no broken requirements.
- Import of `app.backend.main`: 13 routes including FastAPI documentation routes.
- `app/backend/.venv/bin/python -m pytest app/backend/tests -q`: **29 passed**.
- Frontend `npm run build`: TypeScript and Vite build passed.
- Frontend initial `npm test`: **7 passed, 1 failed**. Failure is an assertion about TanStack Query's additional mutation context argument; not yet fixed at this checkpoint.
- Updated Vite/Vitest/plugin packages: npm installation reported **0 vulnerabilities** afterward.
- `npm run start` from `app/`: backend reports listening at 127.0.0.1:8000 and frontend at 127.0.0.1:5173.

Remaining:
- Fix frontend mutation wrapper/test; run full frontend suite.
- Verify real browser and HTTP flows, mobile layout, and count refresh after review.
- Finish explicit API response contracts and operational documentation.
- Final checks and handoff.

Deviations / blockers:
- Direct pip network connection failed in this environment. Installed official PyPI wheels locally via approved curl downloads and offline pip; wheel cache is ignored.
- Raw uvicorn launch was denied local binding in the tool sandbox; the authorized npm start launcher successfully runs both local services.
- Browser connector host is unavailable; native browser UI remains available and will be used for verification.
- ML integration with actual Claude model has not been tested. Mock P0 remains independent and explicitly labelled.

## Checkpoint 2 — Frontend tests and live ingestion verified

- Corrected Analyze mutation wrappers to pass only the intended body/file to API services.
- Frontend Vitest suite: **8 passed** after the fix.
- Verified local frontend returns HTTP 200, and native Chrome renders the Arabic dashboard with Mock banner and empty states.
- Browser end-to-end: entered `التطبيق بطيء` with an explicitly synthetic system; React called FastAPI, persisted record #1, and displayed PERF with null scores as unavailable.
- Browser CSV import: uploaded `frontend/public/demo.csv`, **8 accepted / 0 duplicates / 0 failed**. Reimported the same file: **0 accepted / 8 duplicates / 0 failed**.
- All live records at this checkpoint are Demo; no real model was invoked.

Remaining: verify Explorer review and KPI updates, mobile rendering, explicit response schemas, docs and final tests/build. No new blocker.

## Checkpoint 3 — Review flow, mobile, API contracts verified

- Native Chrome review flow: changed message #9 system name to an explicitly synthetic name, marked review complete, then changed AUTH to PERF. UI retained original AUTH and original system, and showed separate audit entries for the system, review status, and category.
- Dashboard visibly updated to 9 messages, 8 complaints, 88.9% complaint ratio, 8 pending reviews; distributions include the corrected system.
- Inspected dashboard and navigation at responsive **390×844**; mobile menu opens correctly. Closed mobile navigation is hidden from the accessibility tree after a CSS fix.
- Added favicon after observing the single console error was a missing favicon. Refreshed console showed no errors.
- Added explicit Pydantic response models for analytics, systems and model info; OpenAPI schema test passes in the extended suite.
- Lazy-loaded Recharts dashboard route. Production build now produces separate main/dashboard bundles without the previous chunk-size advisory.
- Extended backend tests (33 passed before the final synthetic-provenance guard).
- Added an explicit synthetic-input flag and reserved DEMO- source IDs so fixture inputs remain excluded from real metrics even if analyzed with a Real predictor. Mock records cannot be marked real. Final affected test runs are being collected next.

Remaining: documentation, restart/check the latest backend build, final source/Git review, and final handoff. No actual Claude model inference has been run.

## Checkpoint 4 — P0 verification and operational docs complete

Implemented and verified:
- All six React pages, mandatory frontend/backend stack, nine REST routes with explicit schemas, persistent SQLite and correction audit.
- Synthetic-provenance guard: explicit is_demo and reserved DEMO- IDs cannot enter real aggregates; backend enforces Mock provenance.
- Arabic README with installation/start/test commands, integration notes, pinned Python lock, independent app Git ignores and scoped Pytest cache.
- Persistent tracking files established and kept up to date.

Final automated commands/results after the last functional change:
- `app/backend/.venv/bin/python -m pytest app/backend/tests -q`: **34 passed in 1.49s**.
- `npm --prefix app/frontend test`: **8 passed**.
- `npm --prefix app/frontend run build`: **passed**, TypeScript and Vite production bundles, no chunk-size warning after dashboard lazy loading.
- `pip check`: no broken requirements (earlier environment verification; no Python dependencies changed afterward).
- Dependency installation following Vite/Vitest update reported **0 vulnerabilities**.

Live verification:
- Stopped and restarted both services with `npm --prefix app run start`; persistent nine Demo records and review changes remained present.
- Native Chrome desktop dashboard, analysis, CSV import/reimport and review tested end-to-end.
- Native Chrome mobile emulation 390×844: dashboard, sidebar open/close, model information and systems analysis inspected. Direct route navigation works. Model page explicitly reports evaluation unavailable.
- Live APIs returned success for overview, systems, details, review and model info; frontend HTTP readiness succeeded.

Current data: nine local Demo records (one manual, eight from sample); eight complaints; eight pending reviews. No event publication timestamps were invented. SQLite is ignored, so a fresh checkout begins empty.

Remaining / limitations:
- Real-model acceptance with actual Claude artifacts is deferred; injected adapter tests do not establish real ML correctness.
- PostgreSQL data migration, P1 OCR/EML/clustering and production deployment are out of scope.
- Source and configuration changes remain confined to app; no Claude code was modified.

## Checkpoint 5 — Local delivery checkpoint

- Created implementation commit `ee28839` on independent branch `agent/codex-app`; no push or merge performed.
- Inspected staged source with `git diff --cached --check`: passed. Git working tree was clean after the implementation commit.
- Latest service restart verified persisted data plus live model-info and system-analytics responses. Direct `/model` and `/systems` navigation worked in the mobile browser.
- Stopped both owned preview services cleanly after verification. Restart with `npm --prefix app run start` from the project root.
- Final handoff updated with completed P0 and the exact next Real-model acceptance task. No unresolved P0 blocker; actual Claude-model verification remains pending external artifact readiness.

## Checkpoint 6 — Bilingual UI and richer analytics implemented

User requested a visual/UI refinement and English navigation while retaining Arabic complaint/model content.

Implemented:
- `frontend/src/i18n.tsx` and `translations.ts`: local Arabic/English UI dictionary, persisted language preference, document language and RTL/LTR switching. No translation API and no changes to ML outputs.
- Redesigned shell, bilingual navigation and language toggle; refreshed forms/explorer/model UI.
- Dashboard hero, KPI drilldowns, category donut, time-series controls, ranked systems, source mix, completeness indicators and previous-period panel.
- Systems/category matrix with count drilldowns, search, sorting and alternative cards; Explorer initializes its filters from drilldown URLs.
- Additive overview API fields: reviewed messages, known-system complaints, dated complaints, source totals and equal-length preceding-period comparison only with both date bounds. Division by zero returns null change ratio.
- No database schema or ML contract change.

Verification:
- Extended backend suite: **37 passed** (including independent SQL completeness counts and Riyadh-boundary period comparison with scope/system/source filtering).
- Extended frontend suite: **11 passed** (English switching/persistence/LTR, Arabic input/results retained, drilldown filtering, matrix/cards).
- TypeScript/Vite production build passes.
- An intermediate build/test failed because an existing test fixture lacked the additive overview fields; updated the fixture to the documented response, reran and passed. No unresolved error from that failure.

Remaining: browser visual verification in Arabic/English and mobile, polish observed issues, final docs/handoff. Current local launcher session: 76236.

## Checkpoint 7 — Bilingual browser and analytics interaction verified

- Native Chrome desktop: inspected refreshed Arabic RTL and English LTR dashboard, language switch and persisted English after reload.
- Verified charts retain Arabic category names/system content and Arabic analytical numerals under English navigation.
- Live matrix cell drilldown (system منصة تجريبية ألف × PERF) opened Explorer with the correct filters and exactly one matching Arabic message.
- Live publication-date empty state correctly showed eight undated complaints; “View import activity” switched to actual import timestamps and displayed eight imported complaints at the observed date.
- Clarified the new status metric as `no_review_required_messages` (effective needs_review=false), not proof of an actual human review. Renamed UI to “No further review required”.
- Final functional tests at this checkpoint: **37 backend + 12 frontend passed**, production build passed.
- Browser observations prompted small UI fixes: restore page-top on navigation and disable chart entrance animations for stable data rendering. These are being verified with the frontend checks next.

Remaining: mobile bilingual screenshot/navigation check, final docs and handoff, relevant final frontend test/build.

## Checkpoint 8 — Bilingual refinement complete

- Verified desktop Arabic RTL and English LTR, English persistence after reload, Arabic content preservation, system matrix drilldown and actual import-time chart.
- Verified mobile 390×844 in both languages; English menu opens from the left, Arabic layout returns to RTL. Keyboard navigation opens the menu correctly; native AX clicks in Chrome device emulation were unreliable, so keyboard activation was used.
- Final relevant frontend checks after navigation/chart fixes: **12 Vitest tests passed**; TypeScript/Vite build passed. Backend remains **37 passed** after its last functional change.
- Documented bilingual behavior and analytical denominators. No DB migration, added dependency, translation API, or ML contract change. Data and ML files remain untouched.
- Updated tracking and handoff for session recovery. Only final local Git checkpoint/preview teardown remain.

## Checkpoint 9 — M5 final local delivery

- Final production build after the last mobile-banner CSS adjustment passed.
- Source diff whitespace checks passed. Scope remains exclusively app; no model files or data were changed.
- Owned frontend/backend preview services stopped cleanly. Restart with `npm --prefix app run start`.
- Updated README, integration notes and all three tracking files; no unresolved M5 blocker. Real-model acceptance remains a separate future integration task.

## Integration checkpoint I1 — Histories and local assets preserved

- Source repositories are separate, clean nested repositories: application agent/codex-app at e034f9b; ML agent/claude-ml at a02d2fa. No common root repository or alternate worktrees existed.
- Created `integration/` with dedicated branch `integration/real-ml`; imported both complete histories using unsquashed Git subtree merges. Verified HEAD:app and HEAD:ml tree hashes match the corresponding source commit trees.
- An initial subtree fetch using abbreviated commit IDs was rejected as a remote ref; importing the named branches succeeded and the exact imported commit/tree IDs were verified. No source history was changed.
- Local joblib artifacts are ignored by Claude's Git; copied them into the integrated checkout and verified SHA-256 equality. Copied original SQLite via sqlite3 backup; original remains untouched.
- Existing local frontend dependencies are reused by symlink (no source changes); integration-local Vite cache will avoid writing to the original dependency cache.
- ML inference source confirms local sklearn/joblib loading, a thread-safe per-process model cache, no network call and no Mock fallback. Model version tfidf-baseline-v1; runtime sklearn version must match 1.9.1.

Remaining: backend dependency compatibility, actual model load, integration tests, browser flow and verified final commit. No training or evaluation rerun performed.

## Integration checkpoint I2 — Actual model and automated integration verified

- Installed the backend lock from local wheels in a new integration-only virtualenv. Reused installed ML distributions from Claude's existing environment by copying package files into this new environment; neither source virtualenv was changed. Added requirements-ml.txt with exact inference versions and transitive dependencies (including cloudpickle/narwhals discovered by pip check).
- Actual local inference succeeds with tfidf-baseline-v1: AUTH for OTP, PERF for slowness, null category for praise. pip check reports no broken requirements.
- Backend now defaults to Real and warms the actual local predictor at startup without saving a complaint. Load failures remain visible through model info and inference 503; no Mock fallback. Explicit APP_ML_MODE=mock remains available.
- Added actual-artifact tests for six-field/API schemas, SQLite persistence/restart, corrections, unknown systems, noncomplaints, mixed text, empty input, repeat CSV, missing dates, demo separation, startup loading once and missing-artifact errors. Offline test blocks socket connections while loading the actual pipelines.
- Verified combined suite: **68 passed in 5.83s** (existing app + added actual-model integration + unchanged ML tests; no skips). Existing frontend baseline **12 passed** and production build passed. Additional Real-presentation UI tests are being verified next.
- Recorded copied artifact SHA-256 and originating ML commit in app/MODEL_ASSETS.json. No ML source, weights or evaluation report changed.
- Integration identified two presentation issues: needs_review=false must not claim a completed human review; a real inference on synthetic data must say DEMO without calling it Mock. Small wording fixes and regression tests added; no redesign.
- Known model limitation: mixed “الـ OTP ما يوصلني when I try to login” returns is_complaint=false (0.3165). This is the actual unchanged model output, not an integration success/accuracy claim.

Remaining: finish additional UI checks, actual browser real flow, genuine undated AURA import/reimport, docs and final commit. Verification database is separate from the original user database.

## Integration checkpoint I3 — End-to-end and final functional checks passed

- Native Chrome actual flow: blank validation; Arabic OTP → AUTH; praise → noncomplaint; mixed message accepted with original noncomplaint result; unknown system remains unknown.
- Browser imported four genuine AURA rows from frozen local corpus: 4 accepted; repeat 4 duplicates, no failures. Original dates remain null.
- React dashboard displayed 7 real predictions / 2 complaints; nine existing Mock records excluded. Live proxy responses and independent SQLite query matched; publication trend empty with two undated complaints, import activity counted two. English browsing retained Arabic results.
- Saved real AURA review status in browser; original prediction and audit remained intact. Restarted services; records/correction persisted.
- Connected existing model-info report feature to the exact bundled version, showing Claude's unchanged evaluation text and AI-assisted-reference caveat. Custom artifact locations require explicit report association. Added actual report/hash regression checks.
- Latest verification: **50 app Backend passed in 3.91s; 20 unchanged ML passed in 2.88s; combined 70 passed in 5.14s (no skips); 15 Vitest passed; TypeScript/Vite production build passed.** All pinned dependencies satisfied by no-index pip; pip check passed.
- Resolved Vite fonts 403 caused by reused dependency symlink: replaced it with an independent local node_modules copy. No broad fs/network setting added. Environment-prefixed npm and Python HTTP were denied socket access in the tool sandbox; direct approved npm start and curl successfully completed live checks.
- Updated README and integration/verification notes with runtime pins, offline inference, source pairing, model limits and exact commands. No ML source/artifact/results change or schema migration.

Remaining at this checkpoint: archive verification-only database, restore initial local Demo copy, final source/history/assets checks, commit and preview shutdown.

## Integration checkpoint I4 — Safe delivery state prepared

- Stopped both owned preview services cleanly. Archived complete verification DB as backend/storage/verified-e2e.sqlite3; confirmed 7 real predictions / 2 complaints. Restored normal integrated DB from its initial backup; verified exactly nine Demo messages and no Real test submissions. Original user DB untouched.
- Rechecked SHA-256 of both copied joblib weights and manifest: match MODEL_ASSETS.json and original files. Integrated tracked ml tree equals a02d2fa; no ML diff. Both delivered agent commits remain ancestors.
- Final original-HEAD assertion detected an independent Claude update to 80511e7, only adding .worktrees/ to ML .gitignore, plus a new A4 worktree. Preserved that concurrent work. Verified against the requested delivered commit rather than resetting the original branch. Original app and ML checkouts are clean.
- Updated operational, verification and recovery documents; source whitespace diff check passes. Final reviewed integration commit remains next.

## Integration checkpoint I5 — Verified integration committed

- Created implementation commit `2d6072e` on `integration/real-ml`, containing the verified real-model runtime, local dependency pins, actual-artifact/API tests, minimal presentation corrections, artifact receipt and delivery documentation. No push.
- Staged scope was entirely app/; staged whitespace check passed. All acceptance functionality verified: 50 Backend + 20 unchanged ML + 15 frontend tests; production build; actual browser/API/SQLite flow and restart.
- M6 marked DONE; recovery record updated. Owned preview servers stopped, verification DB archived, normal local DB restored, both source checkouts preserved. No unresolved integration blocker; documented mixed-input/model-quality limits remain.

## Checkpoint M7 — English digits in both languages

- User requested all application numbers in English digits. Updated shared frontend formatters (components/common.tsx): counts, pagination/IDs, imports, percentages and original model scores now use en-US digits/separators; date/time display explicitly uses latn numbering while preserving Arabic labels, Gregorian calendar and Asia/Riyadh. Complaint/source content is preserved.
- Updated existing score assertion and added Arabic/English regression coverage for counts, percentages, scores, input character limit, timestamp digits/timezone and RTL/LTR.
- First test run: all 17 application cases passed, but overall run failed after discovering 13 dependency-package suites through pre-existing untracked node_modules 2 symlink. Restricted Vitest discovery to src tests; rerun: **17/17 passed**. No application tests excluded.
- Initial production build stalled during Tailwind's automatic source scan with that duplicate dependency path present; stopped owned build and scoped Tailwind scanning to src. Final TypeScript/Vite build **passed**, 2308 modules, Vite 369ms. Generated CSS hash remains CWDpAz4B, identical to prior successful build. Duplicate local path preserved untouched.
- Files: frontend/src/components/common.tsx, frontend/src/test/app.test.tsx, frontend/vite.config.ts, frontend/src/styles.css, README and tracking documents. git diff --check passed. Backend, database, artifacts and ML contract unchanged; no Backend rerun needed for this presentation-only change.
- Remaining: none in the requested number-display scope; no preview servers started.

## A4 checkpoint A1 — Safe branch and source import

- Confirmed app integration/real-ml at d835a86, original ML main at 80511e7 and A4 worktree/branch at aa4b39448e867f84e945fa5b0e848beed7ee6984. Existing untracked frontend/node_modules 2 symlink preserved.
- Created integration/a4-marbert from verified integration branch and imported complete A4 branch via ml subtree merge. First subtree command saw stale index stat metadata; after git update-index --refresh confirmed no tracked changes, retry merged successfully. No resets or edits to original branches/worktrees.
- Inspected unchanged six-field inference contract, hf-7way local CPU loader, export manifest/checksums and original report/test code. Runtime uses torch 2.15.0/transformers 5.22.0; HuggingFace Hub needs click >=8.4.2 whereas V1 backend lock has 8.3.0. Isolating A4 backend environment rather than replacing V1 environment.
- Active next step: complete exported safetensors checksum/copy and compatible dependency environment, then wire version-specific report/startup and acceptance tests. No model training or holdout evaluation performed.

## A4 checkpoint A2 — Actual A4 runtime and Python acceptance verified

- Complete export copied locally, including ignored model/model.safetensors (325716998 bytes). All six SHA256SUMS entries match; source and local export unchanged. Added app/A4_MODEL_ASSETS.json receipt; original V1 receipt remains unchanged.
- A4 uses an integration-only .venv-a4 interpreter. Offline wheel installation/package copies hit local filesystem timeouts (including unused transformer modules); stopped those attempts without touching source environments. Current local A4 configuration explicitly references the existing A4 and V1 site-packages via PYTHONPATH, A4 first. A .pth attempt was ignored because the filesystem repeatedly marks newly created files hidden. Partial copies are archived in ignored storage, not used. This local runtime reference must remain available until a normal standalone pip installation is made.
- With that read-only runtime configuration, pip check passes and pip install --no-index -r ml/requirements-a4-inference.txt confirms every required exact pin satisfied. Added a compatible app requirements-a4.txt (without V1 click 8.3 lock conflict). Original .venv preserved.
- Actual A4 predictions: Arabic OTP AUTH (0.9865/0.9064), mixed OTP AUTH (0.9874/0.9070), praise noncomplaint (0.0574), slowness PERF (0.9690/0.8522), mixed payment TRANS (0.9756/0.8972). First manual cold call 7.8644s; subsequent probes 41.9–46.4ms, peak RSS ~1.50GB. Execution probes only, no holdout evaluation.
- Added built-in Node .env loading for local ML_ARTIFACT_DIR/APP_PYTHON settings (caller environment keeps precedence), .env.example, and known-path/version pairing for the original A4 model card. Source report keeps holdout subsets, external proxy and non-blind V1 test separate; API schemas unchanged.
- Added 14 actual A4 app acceptance cases (Arabic/mixed/noncomplaint/blank, exact schema and persistence, CSV duplicates/undated trends, corrections/restart, versions/demo, missing weights 503, asset receipts, cold offline cache/performance, A4→V1 rollback).
- Combined existing + new Python suite: **111 passed, 1 deprecation warning in 34.83s**, no skips. This comprises 64 app Backend + all 47 unchanged ML tests. Warning is Starlette's deprecated AnyIO BlockingPortal alias; no runtime failure. No training or holdout evaluation rerun; report tests render only to temporary files.

Remaining: capture explicit offline API timings, frontend tests/build, real browser workflow/restart/rollback, standalone-env limitation documentation, final integrity checks and commit.

## A4 checkpoint A3 — Frontend, browser and live rollback verified

- Final frontend regression run: **18 passed in 2.54s**; TypeScript/Vite build passed (2308 modules, Vite 254ms), production CSS/JS bundle identities unchanged. Initial raw report import was outside Vite's source boundary; a Node-fs alternative lacked frontend Node typings. Resolved with a byte-identical local test fixture of Claude's card, no new dependency or filesystem allowlist. Cold lazy dashboard test now waits for dynamic imports rather than racing slow filesystem access.
- Dedicated cold offline API probe (socket connects blocked) passed: **4.9879s startup; median Analyze+SQLite 37.0013ms; max 39.8787ms; peak RSS 1,535,344,640 bytes; 8 requests**. Single cached model reused; startup wrote no complaint. These are local execution measurements, separate from Claude's research metrics.
- Existing services occupied 5173 and 8001. Added optional APP_WEB_PORT/APP_API_PORT settings using existing launcher/Vite configuration; verified on 15174/18174 without stopping unrelated services. Defaults remain 5173/8000.
- Actual native Chrome: A4 Arabic OTP and mixed OTP → AUTH, praise → noncomplaint; scores/version persisted and shown. Browser CSV: 4 accepted + 1 invalid; repeat 4 duplicates + 1 invalid. Unknown systems remained unknown; dates remained null. English navigation and English digits preserved.
- Dashboard and independent SQL/proxy checks matched **8 real records (7 A4 + 1 retained V1), 6 complaints; 9 Demo excluded**. Publication trend empty with six undated complaints; import activity counts six. Review changed A4 record #15 system and review status with original scores/system retained and two audit entries.
- Model page displayed a4-marbert-v1, both stored versions, and the original A4 model card. Browser visibly inspected separate holdout_all/random/enriched/codeswitch rows (n=1231/894/337/51); external proxy and NON-BLIND v1_test remain distinct in the same unchanged source report.
- Stopped only owned A4 services, removed ML_ARTIFACT_DIR from local .env, restarted: actual server and React showed **tfidf-baseline-v1**, original V1 report, and retained A4 rows. Real V1 mixed probe persisted with 0.3165/noncomplaint. Restoring A4 configuration and rechecking restart/persistence next.
- Runtime note: one macOS PyTorch multiprocessing resource_tracker cleanup warning appeared on A4 shutdown, in addition to the harmless distributed redirect note; services stopped successfully. No ML code changed to suppress it.

Remaining: restart A4, verify stored correction and selected report/version, restore normal database configuration (archive verification DB), final docs/requirements validation/integrity checks and commit.

## A4 checkpoint A4 — Re-enable, environment checks and release review

- Restored A4 setting and restarted actual services after live V1 rollback. API/model report returned a4-marbert-v1; A4 record #15 retained reviewed system, original system/needs_review and both audit rows. Verification DB now 9 real records (7 A4 + 2 V1), 6 complaints, plus nine Demo; normal DB untouched.
- pip install --no-index -r app/backend/requirements-a4.txt passes with every requested pin satisfied in the explicit local runtime configuration. Confirmed caller environment overrides .env values using Node's actual loader.
- Optional additional run in the original standalone V1 environment (70 historical cases, A4 deselected) stalled during import/collection with no test executed; interrupted after 296.72s. It is NOT reported as passed. This mirrors the filesystem-read constraints that caused package-copy timeouts. V1 acceptance already passed inside the compatible A4 runtime in the 111-case suite, plus real server/API/React rollback and persistence. No source environment altered to work around this.
- README and both integration notes now document model selection/restart, rollback, actual metrics with dataset labels, exact pins, local referenced-runtime limitation, current ports, test commands and no research reruns. A4_INTEGRATION_VERIFICATION.md records full observed outcomes and failures.

Remaining: stop owned services, remove verification DATABASE_URL from normal .env while keeping A4 enabled, final checksums/source/history checks and commit. Original unrelated services stay untouched.

## A4 checkpoint A5 — Final startup and safe normal-data configuration

- Fixed observed cold-start proxy race in launcher: wait for local Backend diagnostics before starting Vite, with 120s timeout and proper Ctrl+C/child failure handling. A model error still exposes diagnostics and starts UI; no model fallback.
- Actual final normal startup verified log order: A4 model loaded → Backend startup complete → diagnostics 200 → Vite ready. Caller-environment precedence passed. Live proxy showed A4 verified and exact A4 report; real overview 0/0 and observed_versions empty, proving no warmup/test records in normal data.
- Removed verification DATABASE_URL from app/.env, retained A4 selection, explicit package references and collision-free 15174/18174 ports. Normal DB remains initial nine Demo records; dedicated a4-e2e.sqlite3 archive holds nine real cross-version probes, six complaints, nine Demo and review audit.
- Stopped owned preview services. Unrelated existing services/tabs/source worktrees preserved. Final A4/V1 SHA receipts and source A4 export hashes match; integrated tracked ML tree equals aa4b394; no ML working diff. Original source repositories clean. integration/real-ml still d835a8657a426f22e3bc5d0f979b91b7b411ecc3. API/TypeScript schemas unchanged; report test fixture byte-identical to source.
- All mandatory acceptance tests passed in the compatible runtime; local package-reference constraint and the optional old-environment import stall are documented without claiming standalone portability. No research training or holdout evaluation rerun.

Remaining: final staged scope/whitespace inspection and verified integration commit, followed by completion handoff.

## A4 checkpoint A6 — Verified integration committed

- Created commit `03a006f` on integration/a4-marbert containing all verified app integration, actual A4 tests, runtime/report selection, startup readiness, environment example/pins, checksums and documentation. All staged changes app-only; whitespace check passed. ML delivery remains the exact aa4b394 subtree; V1 integration branch preserved.
- M8 marked DONE; recovery handoff records exact startup/rollback, 111 Python + 18 frontend passing tests and production build, separate verification data, source preservation, dependency-reference constraint and optional old-environment test interruption. No invented test outcome.
- A4 remains selected locally, verification DATABASE_URL removed; owned previews stopped. No push or unrequested work.

## Environment checkpoint E1 — Working setup preserved; isolated candidate started

- Inspected verified integration/a4-marbert at 01f0b43, current environment/config and recovery documents. Original working setup still uses explicit external package references.
- Created integration/a4-environment branch and copied local .env to ignored backend/storage/a4-environment-recovery/working-a4.env. Candidate is backend/.venv-a4-standalone; working .venv-a4/.venv and source runtime environments are untouched.
- Official PyPI JSON endpoints for pinned transformers 5.22.0 and torch 2.15.0 returned HTTP 200 through approved curl. Will use fresh wheel downloads rather than previously timing-out package copies/cloud-placeholder wheels, then install with pip into the new environment.
- No active launcher configuration change, training, model/dataset/API/feature edits, or P1 work.

## Environment checkpoint E2 — Fresh standalone installation and isolation audit passed

- Downloaded metadata for all 60 compatible direct/transitive packages from official PyPI. Selected CPython 3.12/macOS arm64 wheels; generated requirements-a4-macos-arm64-py312.lock with every version and SHA-256, plus a4-wheel-manifest.json with official URLs/sizes/hashes. Minimum wheel platform is macOS 14 for Torch/SciPy.
- Downloaded 261,679,002 bytes of wheels through approved curl. One premature candidate pip attempt ran while Torch was still downloading; size/SHA validation and pip's hash enforcement rejected the incomplete file. No package/config from the working setup changed. After Torch finished, all 60 complete wheels matched official SHA-256; only then retried installation.
- Fresh project backend/.venv-a4-standalone successfully installed all 60 pinned packages from the verified local wheel cache with --require-hashes --only-binary=:all: --no-index. This uses actual installed packages, not copies, symlinks or PYTHONPATH references. Original environments preserved.
- Added verify_a4_environment.py operational audit. Executed using candidate Python -I: all distribution locations and 15 critical module origins are inside the candidate; no external site/dist-packages, no external .pth/egg links, user/system site disabled, no PYTHONPATH/PYTHONHOME. All core pins match source requirements/lock; pip check passed; all 10 V1/A4 receipt files passed SHA/size checks.
- Retained an ignored project-local .wheelhouse-a4 with 60 hash-verified wheels for repeat offline installation. Candidate runtime does not import from or depend on the cache.

Remaining: collect candidate full Backend/ML tests, frontend tests/build, explicit offline startup/inference and live V1 rollback; switch .env only after candidate passes; docs and commit. Working .env remains unchanged so far.

## Environment checkpoint E3 — Standalone acceptance passed; active setting switched

- Candidate-only suite: **111 passed, 1 existing deprecation warning in 21.47s** (64 Backend + all 47 unchanged ML), no skips, using candidate Python -E -s without external package configuration. Frontend **18 passed in 1.92s**; production build passed (2308 modules, Vite 229ms), identical bundles.
- Additional clean offline process denied all socket/DNS calls and any reads from external site/dist-packages. Actual A4 API startup/inference passed (cold 6.1068s), Arabic/mixed/praise/PERF/TRANS outputs unchanged; V1 rollback and A4 re-enable passed with six records persisted only in a temporary DB. Network attempts=[] and external package reads=[]. Original datasets/model unchanged.
- Original A4 SHA256SUMS directly verified 6/6, in addition to all 10 V1/A4 receipt assets. Isolation audit also correctly rejects an injected PYTHONPATH setting.
- Only after these checks, changed local APP_PYTHON to backend/.venv-a4-standalone/bin/python and removed PYTHONPATH/PYTHONHOME. Archived the old helper text under ignored recovery storage; original environments/config backup preserved but no longer required for normal A4 or V1 use.

Remaining: actual two-service startup with selected environment, final normal config, complete fresh-install/offline instructions, final integrity checks and commit.

## Environment checkpoint E4 — Selected standalone runtime starts the complete app

- Actual npm launcher used the newly selected standalone interpreter with no Python path override. Log order: A4 loaded from local export → FastAPI ready on 18174 → diagnostics 200 → Vite ready on 15174. Torch log origin is inside the standalone site-packages.
- Live React HTML and Vite API proxy succeeded; model-info reports a4-marbert-v1/verified and the exact original A4 report. Real overview remains 0/0, normal SQLite still nine Demo messages; no verification data was written to normal DB.
- Final ordinary (non -I) audit also passed, proving normal startup is local-only. Audit JSON now includes pip-check result and verifies exact full lock/manifest entry agreement. No packages loaded from any old environment; old environments/config remain recovery-only.
- Added complete ENVIRONMENT_SETUP.md (fresh online/offline install, supported target, assets, audit, startup/rollback/tests) and ENVIRONMENT_VERIFICATION.md (executed outcomes/provenance). Updated README, env example and current integration notes; old A4 verification constraint retained as clearly superseded history.

Remaining: stop owned preview, final source/asset/preservation checks, completion docs and commit. No P1/model/dataset/API/website-feature changes.

## Environment checkpoint E5 — Safe delivery review complete

- Owned preview pair stopped cleanly after successful selected-environment startup. Existing Torch semaphore cleanup warning observed as before, no stop/restart failure. Unrelated services untouched.
- Final checks: A4/V1 assets and ML tree unchanged; app Backend API/services/schemas, frontend feature code/types and launcher have no diff from 01f0b43. Old A4/V1 branches, runtime directories, prior working config and original source worktrees preserved. Active .env contains only standalone interpreter selection with no Python path override; normal DB exactly nine Demo records.
- Updated all tracking/recovery records and current setup docs. Fresh/repeat install is fully hash-locked for the documented target; no P1, training/evaluation rerun or feature change. No unresolved blocker.

Remaining: final staged scope/whitespace check and verified commit/completion checkpoint.

## Environment checkpoint E6 — Verified standalone environment committed

- Created implementation commit `9ea34e0` on integration/a4-environment: full hash-locked dependencies, official wheel provenance, isolation/asset audit, standalone env example/ignores, setup/verification docs and recovery tracking. Staged scope entirely app; whitespace checks passed. No push.
- M9 marked DONE. Selected environment is self-contained with no external site-packages/PYTHONPATH requirement; A4 and V1 rollback verified. 111 Python tests, 18 frontend tests, production build, real offline/no-external-read probe and actual two-service startup passed.
- Original source/model/dataset/API/UI files and old environments preserved; normal database unchanged; owned previews stopped. No unresolved blocker or P1 work.

### P1 checkpoint P1-1 — source integration verified

- Created integration/p1 from stable environment commit 3b2c2cf; merged Claude branch agent/claude-ml-p1 (d8ffad4) with unsquashed subtree history. Integrated ml tree hash equals source tree.
- Confirmed ml/infer.py, A4 export and A4 dependency pins have no differences from stable application checkpoint. Source agent branches preserved. No prior P1 app implementation found.
- Backed up active .env and normal SQLite under ignored backend/storage/p1-recovery. Existing standalone A4 interpreter and unrelated dependency symlink untouched.
- Reviewed P1 pipeline, OCR/system contracts, synthetic-only evaluation caveats and tests. No P1 application/runtime tests claimed yet.
- Next: independent P1 environment, actual local OCR support probe, additive backend implementation. Potential documented limitation: Vision may fail in sandbox; verify host before selecting a documented fallback.

### P1 checkpoint P1-2 — independent runtime and first regression run

- Installed 66 hash-pinned official packages into separate .venv-p1; original .venv-a4-standalone unchanged. Isolated environment audit passed: local-only imports, pip check clean, 10 model receipts verified. Added optional fully pinned EasyOCR fallback (77 packages) and copied ignored OCR weights after checking Claude's four hashes. No ML source modified after subtree import.
- Implemented initial additive OCR draft/provenance tables, typed extraction/analysis routes, immutable pipeline persistence and existing review integration; extended Analyze with image preview/extract/edit/confirm and system evidence. These P1 features are still under verification.
- Existing Backend unit tests: 37 passed, 27 integration cases deselected. First full run: 226 passed /20 failed, comprising 14 unchanged ML Vision tests +6 new app Vision-dependent cases. All failures were actual Vision engine_error in this sandbox; not counted as passes or changed to fake OCR.
- Independent real EasyOCR extraction of synthetic err00.png passed with local weights and network helper blocked, engine easyocr-1.7.2/ar+en/canvas1600. No accuracy claim. Running complete Backend with documented fallback next.
- Blockers discovered: shell and Node tool application startup load A4 but localhost bind fails EPERM; native/browser tool host unavailable. Initial Vitest worker startup timed out; trying single-thread pool and will diagnose dependency/runtime issue. Build still running. Full browser acceptance pending, not claimed.

### P1 checkpoint P1-3 — application/API acceptance and build verified; host acceptance blocked

- Backend now93/93 passing (64 original +29 P1) with actual local EasyOCR/canvas1600 and unchanged a4-marbert-v1. Covers original+corrected OCR/audit, immutable evidence, strict schemas, unknown/ambiguous/multiple names, redaction, drafts, upload limits/decompression-bomb header, dedup, review, restart, offline, dates/demo analytics and explicit errors. Existing CSV/A4/V1 suites pass.
- Frontend26/26 passing using default npm test; TypeScript/Vite production build passed. Preview/extract/edit/confirm and stale-image/error/pending/English controls verified by component tests; API doubles are explicitly not browser E2E. One existing lazy dashboard assertion now waits for the actual asynchronous route heading rather than racing the import.
- Full Backend+ML attempt at preceding app revision:233 passed14 failed/no skips; ML portion141/155 pass,14 Vision execution failures. Source ML remains exact d8ffad4. No tests altered/skipped to hide the host limitation. Final additional upload-header case and targeted final Backend suite passed.
- Isolated optional P1 environment audit:77 local pinned distributions,25 critical modules, pip clean,10 original V1/A4 receipts +2 EasyOCR hashes verified. Original A4 SHA256SUMS6/6 match. Additive schema probe preserved every old complaint/correction row and SQL definition (9 Demo).
- Three official Absher App Store images passed actual OCR→MARBERT→systems→SQLite APIs, all Demo. Small text/scenery yielded substantial OCR errors; one services page was classified as a complaint. Source URLs/hashes/observations recorded, no accuracy/CER/WER claimed. Public UI images are not field complaint captures.
- Full browser acceptance is BLOCKED: localhost bind EPERM, native/browser host unavailable, installed headless Chrome cannot launch. A4 does load before the bind failure. Vision initializes but recognition fails engine_error in sandbox. Exact remaining normal-host steps and all results: P1_INTEGRATION_VERIFICATION.md.
- Current local settings select .venv-p1+A4+explicit EasyOCR fallback; temporary verification DATABASE_URL removed, normal DB rows preserved. Stable A4 interpreter/config and original repositories/worktrees retained. No email/EML, training, holdout evaluation or redesign.
- Next: final preservation/documentation checks and commit this verified implementation checkpoint. M10 remains IN_PROGRESS until real host/browser acceptance.

### P1 checkpoint P1-4 — final preservation and recovery checkpoint

- Final independent SQL comparison: normal DB retains exactly9 Demo complaints and3 corrections equal to pre-task backup; no Real/P1/draft verification rows leaked into it. Source Git worktrees clean; integrated ml tree still exact d8ffad4, A4 infer/export/pins unchanged. Temporary DATABASE_URL removed.
- Default frontend command26/26 passed after final shared-formatting/fixture changes; production build passed. Final Backend93/93 passed after bounded-image validation. P1 full environment audit77 packages/25 imports/10 model+2 OCR hashes passed.
- Optional preserved old A4 environment re-audit stalled during pandas file reads and was interrupted, not counted as passing. Its dependency metadata/location checks completed; old packages were not replaced. New P1 runtime and A4/V1 rollback are verified. No preview server remains running.
- P1 setup, contracts, qualitative public screenshot observations, exact host blockers and recovery records finalized. Commit is an implementation checkpoint, not a claim that blocked browser/normal-host Vision acceptance is complete.

### P1 checkpoint P1-5 — implementation committed

- Verified implementation committed as7175581 on integration/p1 (38 app files; original ML source imported separately by subtree). No weights, environment directories, databases, public screenshot binaries or unrelated dependency symlink staged.
- Plan/handoff record the exact commit and first remaining host acceptance step. M10 remains IN_PROGRESS; normal-host Vision/full155 ML and actual browser/localhost acceptance remain BLOCKED, not falsely marked complete.
