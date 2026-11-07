# Integration acceptance record — 2026-10-30 (Asia/Riyadh)

All commands below were executed from `Project/integration/`. This record describes application execution verification, not a new scientific model evaluation.

## Automated evidence

| Command | Observed result |
|---|---|
| `app/backend/.venv/bin/python -m pytest -c app/backend/pytest.ini app/backend/tests -q` | 50 passed in 3.91s |
| `app/backend/.venv/bin/python -m pytest -c app/backend/pytest.ini ml/tests -q` | 20 passed in 2.88s, no skips; ML tests unchanged |
| `app/backend/.venv/bin/python -m pytest -c app/backend/pytest.ini app/backend/tests ml/tests -q` | 70 passed in 5.14s, no skips |
| `npm --prefix app/frontend test` | 15 passed |
| `npm --prefix app/frontend run build` | TypeScript and Vite production build passed |
| `app/backend/.venv/bin/python -m pip check` | No broken requirements |
| `app/backend/.venv/bin/python -m pip install --no-index -r app/backend/requirements-ml-tests.txt` | All pinned runtime/test dependencies satisfied locally |

`backend/tests/test_real_integration.py` adds 13 cases using Claude's actual artifacts: exact six-field/API schemas; stored values; actual Arabic AUTH/PERF/noncomplaint/mixed predictions; blank input 422/no write; startup warmup/no write; two pipeline loads only; cold artifact load with socket connections blocked; database restart and corrections; Mock/synthetic separation; CSV repeat and bad rows; missing publication dates and Riyadh day boundary; missing model 503/no fallback; asset SHA-256; original evaluation report pairing/display. Existing unit tests cover malformed predictor output and partial CSV errors as well.

Frontend adds three Real-presentation tests using an observed output fixture for UI behavior. These frontend tests substitute REST responses; they do not claim to execute ML. The separate browser flow below uses the actual running Backend/model/database.

## Actual browser and live API evidence

Started both local services with `npm --prefix app run start`. Native Chrome used the React website through Vite's /api proxy.

1. Real banner shows `tfidf-baseline-v1`; initial real dashboard excludes nine pre-existing Demo messages.
2. Empty React input is blocked with a visible validation message.
3. Submitted Arabic OTP complaint: AUTH, complaint_score 0.978, category_score 0.8864; unknown system remains unknown. Result persisted and displayed by React.
4. Submitted praise: noncomplaint, complaint_score 0.0262, category/category_score null.
5. Submitted mixed OTP message: accepted; actual output noncomplaint, score 0.3165. Recorded as a model limitation, not silently corrected.
6. Imported four genuine AURA corpus rows (record IDs S00001/S00181/S00252/S00343, source app ALKAHRABA) through the browser: 4 accepted/0 duplicates/0 failed. Reimport: 0 accepted/4 duplicates/0 failed. No source dates exist or were invented.
7. Dashboard: 7 real predictions, 2 complaints, 9 Demo excluded. Independent SQLite query returned exactly (7,2). Of the four AURA rows, one was classified UX and three noncomplaint; this is inference on existing corpus rows, not a fresh evaluation set.
8. Publication trend: no points and 2 undated complaints. English navigation kept Arabic categories/results; “View import activity” used actual imported_at and counted 2 complaints on the observed import day.
9. Review queue: opened the real AURA UX result, saved no-further-review status; queue cleared, original prediction retained needs_review=true, audit stored true→false.
10. Restarted both services. Seven real records, original prediction and review audit remained saved. Model info displayed successfully loaded local version and Claude's original evaluation report including AI-assisted-label caveat.
11. Live responses retrieved through the Vite proxy with curl were validated against SQLite and direct actual predictions. The served report matched ml/reports/evaluation.md verbatim.

Only native Chrome/CUA was used for browser interactions. No hosted service, external inference API or paid API was used.

## Environment issues resolved

- Shell pip network access was unavailable. Installed backend wheels offline, then copied the exact installed ML package distributions from Claude's existing environment into a new integration-only virtualenv. Source environments were preserved. The committed pins validate with no-index pip install and pip check.
- Initial shared node_modules symlink caused Vite font requests outside its serving allowlist (403). Replaced it with an independent local dependency copy; browser rendering and final tests/build passed. Vite cache is integration-local.
- Environment-prefixed launcher and Python live HTTP attempts were denied local socket access by the tool sandbox. The already-authorized direct npm launcher and curl commands succeeded. No application workaround or broader network permissions added.

## Data, history and scope

Ignored weights and manifest match `MODEL_ASSETS.json` and the original delivery. The imported tracked ml tree remains exactly Claude's commit tree. Both agent commits remain ancestors of the integration branch; neither original checkout/branch is reset or changed.

The verification database is archived as `app/backend/storage/verified-e2e.sqlite3` (ignored). The normal integrated database is restored from its initial nine-Demo backup after testing, avoiding test submissions in default real analytics. Source databases remain untouched. Tests use temporary SQLite files; no migration needed.

P1, retraining, deployment, PostgreSQL migration and model-quality improvements remain out of scope. Install dependencies once; inference afterward is local/offline. A new checkout must receive the original ignored joblib weights rather than retrain them.

Final source inspection observed Claude's separate branch advancing independently to `80511e7` (only `.worktrees/` added to ML .gitignore) and a new `agent/claude-ml-a4` worktree. Neither was modified by integration. The integrated ML snapshot intentionally remains exactly the user-specified `a02d2fa`, and original weight hashes still match. An initial final assertion expecting the original branch HEAD to remain fixed detected this concurrent change; checking against the delivered commit instead confirmed no integration drift.
