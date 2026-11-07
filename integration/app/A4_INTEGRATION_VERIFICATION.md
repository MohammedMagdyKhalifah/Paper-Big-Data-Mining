# A4 application integration acceptance — 2026-10-30

Historical A4 integration record. The referenced-runtime limitation below was subsequently resolved by M9; current setup/verification is in ENVIRONMENT_SETUP.md and ENVIRONMENT_VERIFICATION.md. Original outcomes here are retained as history.

This is execution verification of the existing React/FastAPI/SQLite application. No training, model selection or holdout evaluation was rerun.

## Delivery and preservation

- Active branch: integration/a4-marbert, forked from verified d835a86 on integration/real-ml. V1 integration branch preserved.
- Imported Claude's full aa4b39448e867f84e945fa5b0e848beed7ee6984 through existing ml subtree (merge e7d8ee1). Tracked ml tree matches that commit; no application-authored ML edits.
- Full export: ml/artifacts/a4/export/a4-marbert-v1/. All six SHA256SUMS entries verified, including copied ignored model/model.safetensors, SHA256 492b0585b9310e6e43e58a653c507a17144bbb2d9be4f24d707cbf57d7bfe25b, 325716998 bytes. app/A4_MODEL_ASSETS.json records the copied bundle. Original V1 MODEL_ASSETS.json/weights unchanged.
- Existing original app/ML branches/worktrees and databases preserved. Unrelated frontend/node_modules 2 symlink preserved. No push.

## Runtime configuration and compatibility

Local ignored app/.env selects APP_ML_MODE=real, ML_ARTIFACT_DIR=ml/artifacts/a4/export/a4-marbert-v1, APP_PYTHON=backend/.venv-a4/bin/python, HF_HUB_OFFLINE=1 and TOKENIZERS_PARALLELISM=false. Node's built-in .env loader is used; no new runtime package. Caller environment takes precedence. Optional ports allow parallel verification: frontend 15174, Backend 18174, because existing services occupied ordinary ports. Those services were left running.

A4 core pins are Claude's unchanged requirements-a4-inference.txt (torch 2.15.0, transformers 5.22.0, tokenizers 0.23.3, safetensors 0.8.0, sklearn 1.9.1). App requirements-a4.txt includes those plus compatible Backend/testing versions. V1 .venv/lock preserved; its click 8.3 pin must not be imposed on HuggingFace Hub requiring click >=8.4.2.

**Local dependency limitation:** filesystem timeouts prevented complete wheel/package copies into a standalone environment. Current integration-only .venv-a4 interpreter explicitly references existing A4 runtime and V1 Backend site-packages via PYTHONPATH in ignored .env. These source environments were not modified. Keep both directories available; for portable deployment install requirements-a4.txt normally into .venv-a4 and remove the local PYTHONPATH override. Exact required pins validate with pip install --no-index -r app/backend/requirements-a4.txt, and pip check reports no broken requirements. This fully tested local reference arrangement is not claimed to be a self-contained dependency installation. Failed partial copy attempts are unused under ignored storage. A .pth approach was discarded because this filesystem reapplies the hidden-file flag, which Python skips.

## Automated checks

| Executed check | Result |
| --- | --- |
| A4 environment: pytest app/backend/tests ml/tests -c app/backend/pytest.ini -q | 111 passed in 34.83s: 64 app Backend + all 47 unchanged ML tests; no skips |
| A4 cold offline API test, rerun with -s for measurements | 1 passed in 6.76s |
| npm --prefix app/frontend test | 18 passed in 2.54s |
| npm --prefix app/frontend run build | TypeScript/Vite passed; 2308 modules, Vite 254ms |
| Optional original standalone V1 environment retry | Interrupted during import/collection after 296.72s; no tests ran. Not claimed as passed. Full V1 acceptance and live rollback passed in compatible runtime. |
| Inference/app dependency validation | Required exact pins satisfied offline; pip check passed |

New A4 app tests cover exact prediction/API schemas, actual Arabic/mixed/noncomplaint output, blank input/no write, SQL persistence, import/reimport/invalid rows, undated trend semantics, review/audit/restart, stored versions/Demo exclusion, missing weights 503 with no fallback, A4/V1 asset hashes, original A4 report pairing and cached offline startup/performance. The original V1 acceptance suite remains. Frontend adds one A4 report/version presentation case using a byte-identical local snapshot of Claude's card. Existing lazy dashboard tests now wait for dynamic imports to avoid a filesystem-dependent timing race. No API response model or frontend production page was redesigned.

Initial frontend attempts exposed an external raw-file import denial and missing Node typings when trying Node fs; both resolved using the in-scope test fixture without broadening server access or adding dependencies. Final CSS and production JS bundle identities match the pre-A4 app, since all page logic remains compatible with the frozen ML contract.

One Starlette/AnyIO BlockingPortal deprecation warning occurred under the newer compatible runtime. PyTorch printed a macOS distributed redirect note and one resource_tracker semaphore cleanup warning during an owned shutdown. These did not fail tests or stop clean service restart. No model code was changed to suppress them.

## Offline / performance evidence

A fresh subprocess blocked socket connects before importing/loading A4, then started FastAPI in TestClient, verified no warmup record, submitted eight actual Analyze+SQLite requests and checked cached model identity. Observed:

- Cold app startup: 4.987877417 seconds.
- Median Analyze API including SQLite write: 37.001271 ms.
- Maximum of 8 requests: 39.878667 ms.
- Peak process RSS: 1,535,344,640 bytes (macOS ru_maxrss bytes).
- Device: local CPU; these are execution measurements, not research metrics or promises for other hardware.

Earlier standalone cold import/probe was 7.8644s; warm individual inference 41.9–46.4ms. No network inference, model download or cloud API was used. Installation is separate from offline runtime.

## Real browser, proxy and persistence

Native Chrome separate tab → React at 15174 → Vite /api proxy → FastAPI at 18174 → actual MARBERTv2 → isolated SQLite → React.

1. Real banner/version a4-marbert-v1; Arabic OTP AUTH (0.9865/0.9064), mixed OTP AUTH (0.9874/0.9070), praise noncomplaint (0.0574, null category). Results displayed using English digits. Unknown systems stayed unknown.
2. Browser CSV: 4 accepted/0 duplicates/1 invalid row; repeat 0 accepted/4 duplicates/1 invalid. Source dates kept NULL.
3. Dashboard/independent SQL matched 8 real records (7 A4 + 1 retained V1), 6 complaints; 9 Demo excluded. Publication trend empty with 6 undated complaints; import activity counts 6. All verification inputs are controlled examples in a dedicated database, not a new research test set.
4. Reviewed A4 record #15: system changed to a verification name and needs_review false. Original system, scores/version/needs_review retained; two audit entries persisted. English navigation preserved Arabic results and English digits.
5. Model page displayed current A4 and both stored versions, plus Claude's source model card verbatim. Browser visibly inspected holdout_all/random/enriched/codeswitch rows separately. External AURA proxy and v1_test_NOT_BLIND have distinct named sections; AI-assisted-label caveat retained. No dataset pooling or invented evaluation numbers.
6. Stopped owned servers, removed ML_ARTIFACT_DIR from local .env, restarted. Both API and the same React page showed tfidf-baseline-v1 and the original V1 evaluation. Stored A4 records remained. A new real V1 mixed probe persisted noncomplaint at 0.3165.
7. Restored ML_ARTIFACT_DIR and restarted A4. Version/report and original correction audit persisted. SQLite now has 9 real records: 7 A4 + 2 V1, 6 complaints; plus the unchanged 9 Demo. App response schemas and training/evaluation files remain unchanged.

## Research metrics display

The displayed authoritative source is ml/reports/a4_model_card.md, unchanged from aa4b394. Its holdout_all row records n=1231, end-to-end macro-F1 0.6896, gate macro-F1 0.9125 and category macro-F1 0.7290. The random/enriched/code-switch subsets, external human AURA proxy and NON-BLIND secondary V1 test retain their original labels and separate results. These are Claude's already-computed metrics, not recalculated by the application. AI-assisted reference labels are not human gold.

## Rollback / release scope

Remove ML_ARTIFACT_DIR from both app/.env and any exported caller setting, then restart both services. Default ml/artifacts selects V1. Restore the A4 setting and restart to re-enable MARBERTv2. Cached models intentionally do not switch inside a running process. Missing A4 fails explicitly, never silently falls back to Mock or V1. Older stored predictions are not overwritten or reanalyzed.

After verification, the dedicated a4-e2e.sqlite3 is retained as an ignored execution archive; the DATABASE_URL override is removed from normal app configuration. No DB migration. Normal source databases are untouched. No P1 features, UI redesign, new infrastructure or training changes.

## Final startup and normal-data checkpoint

A startup race observed during service restarts allowed Vite to accept browser requests before ML warmup finished. The launcher now waits for /api/models/info (up to 120s) before starting Vite. Actual final startup logs show model load → FastAPI startup complete → successful diagnostics GET → Vite ready, with no initial proxy error. A model error still makes diagnostics reachable and starts the UI for inspection; there is no fallback. Caller-environment precedence was also verified against Node's loader.

After removing the verification DATABASE_URL override, restarted with normal local configuration: A4 verified, exact A4 source report, observed_versions empty, real dashboard 0 messages/0 complaints. Normal SQLite still contains only the initial nine Demo records; warmup added nothing. Archived a4-e2e.sqlite3 contains the completed cross-version browser/restart/rollback evidence. Owned previews stopped at delivery; unrelated services preserved.
