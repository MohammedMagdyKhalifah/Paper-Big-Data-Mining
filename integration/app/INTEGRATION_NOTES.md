# Real ML integration — V1 and A4

Active checkout: Project/integration/, branch integration/a4-environment (verified A4 integration branch retained). Preserved V1 branch integration/real-ml at d835a86. Original app/ and ML repositories/worktrees were not reset or overwritten. A4 subtree imports Claude aa4b394; imported tracked ML content matches exactly. See A4_INTEGRATION_VERIFICATION.md for current acceptance evidence, INTEGRATION_VERIFICATION.md for the historical V1 acceptance record, and PROGRESS.md for chronological outcomes.

## Frozen boundary and model selection

The application calls only ml.infer.predict_text(text), with the unchanged six fields. No API response schema, database schema or frontend page logic changed. REST metadata wraps the prediction and preserves model_version, original_prediction, source and timestamps; corrections change effective fields while retaining original scores/provenance.

APP_ML_MODE=real is the backend default. ML_ARTIFACT_DIR selects A4; absent setting selects original tfidf-baseline-v1 at ml/artifacts. The local .env and .env.example opt into A4. Node's built-in loader reads app/.env; caller environment takes precedence. APP_PYTHON may select an isolated interpreter, optional APP_WEB_PORT/APP_API_PORT avoid existing local services. Relative Python paths resolve from app/, relative artifact paths from integration/. Default ports remain 5173/8000; current local instance uses 15174/18174.

Startup warmup loads the actual local model without saving a complaint. Process cache is reused. Changing the model setting requires service restart. A Real load/inference/contract failure never selects Mock or V1 silently: Analyze returns 503, CSV returns explicit stopped/partial status, model-info retains diagnostics. Mock is explicitly selected and always Demo.

## Assets and dependencies

V1 weights/manifest/receipt and .venv remain intact. Complete A4 export, including ignored safetensors, is copied into ml/artifacts/a4/export/a4-marbert-v1, all SHA256SUMS verified. A4_MODEL_ASSETS.json pins the delivered bundle; no training, research labels, holdout evaluation or artifacts were changed. Missing weights must be transferred from the approved export, not rebuilt/retrained during app setup.

Claude's requirements-a4-inference.txt and core model versions remain unchanged. Normal A4/V1 execution now uses the self-contained app/backend/.venv-a4-standalone, with all 60 direct/transitive packages installed from official hash-verified wheels. Complete platform lock and wheel provenance manifest are under backend/. No external site-packages, PYTHONPATH/PYTHONHOME or external .pth/egg references are needed. Old environments are recovery-only. See ENVIRONMENT_SETUP.md and ENVIRONMENT_VERIFICATION.md for fresh/offline installation, target scope and verified results.

## Evaluation display and datasets

Known A4 artifact path plus successful a4-marbert-v1 inference pairs with Claude's original ml/reports/a4_model_card.md; original V1 path/version pairs with evaluation.md. Arbitrary custom paths need explicit APP_EVALUATION_REPORT and APP_EVALUATION_MODEL_VERSION as before. The source report is displayed verbatim as plain text, without invented or recomputed metrics.

A4's holdout_all, random, enriched and code-switch subsets, external AURA proxy and v1_test_NOT_BLIND/NON-BLIND secondary comparison remain separately named in the original card. No pooling or claim that different test sets are interchangeable. Labels are AI-assisted reference labels, not human gold. Operational dashboard totals are stored-message counts, not model-quality evaluation.

## Provenance, dates and rollback

Mock records and explicit synthetic/DEMO- inputs stay Demo, excluded from default real analytics. Unknown systems remain unknown unless source metadata or human review supplies a name. AURA/missing original dates remain NULL; publication trends omit them with a missing-date count, import trends represent ingestion activity only. English digits 0–9 and bilingual RTL/LTR behavior remain verified.

Rollback: stop owned services, remove ML_ARTIFACT_DIR from app/.env and any caller export, restart. Original V1 is loaded and its report shown. Restore the setting and restart for A4. Older predictions/corrections are not overwritten or reanalyzed. Actual server/API/browser rollback and re-enable were verified with stored predictions from both versions.

No database migration, UI redesign, OCR, EML, clustering, model training, paid API or unrelated infrastructure added. Verification uses an ignored separate SQLite archive; normal app/source databases are preserved.
