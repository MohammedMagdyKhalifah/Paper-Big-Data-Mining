# Integration Notes

## Scope and ownership

This implementation follows the original application plan with the user's explicit React/FastAPI override. It contains no Streamlit. All source, configuration, tests, documentation and local storage are under `app/`. Claude's `ml/` has not been edited. Git is independent inside `app/`, branch `agent/codex-app`, as approved by the user.

## Frozen ML boundary

`backend/services/classifier_adapter.py` owns the sole ML boundary. Real lazily imports `ml.infer.predict_text`. Mock never imports it. The six-field dict contract is unchanged: required strict booleans, nullable numeric scores in [0,1], nullable six-category code, nonempty model_version. Noncomplaints must have null category. Invalid model output/loading/inference errors become explicit integration errors, never Mock fallback.

Application REST metadata (message IDs, source, times, demo scope, original_prediction and corrections) wraps the prediction and does not add requirements to Claude's function. `source_app` is metadata, not ML extraction. `system_reviewed` distinguishes a human-corrected effective name from original metadata evidence.

HTTP 503 is returned for failed single inference; CSV returns a structured stopped/partial report if inference fails after some rows. Review and viewing existing data remain usable.

Real acceptance is **not yet completed**. The adapter was tested with injected functions and deliberately missing modules/weights only. No actual Claude artifacts were loaded and no scientific scores were generated. Application completion does not imply that the ML research is complete.

## REST contract

OpenAPI is available at `/openapi.json` and `/docs` on the backend. Response schemas are explicit Pydantic models. Frontend TypeScript interfaces mirror them.

| Method | Path | Request | Response |
|---|---|---|---|
| POST | /api/complaints/analyze | JSON text, optional source_id/source_app/original_event_time/is_demo | message, duplicate |
| POST | /api/complaints/import | multipart file; optional is_demo flag | accepted, duplicates, failed, processed, errors, stopped, integration_error |
| GET | /api/complaints | filters + q/category/is_complaint/needs_review/page/page_size | items, total, page, page_size |
| GET | /api/complaints/{id} | integer ID | current record, original_prediction and corrections |
| PATCH | /api/complaints/{id}/review | is_complaint, category, system_name, needs_review | updated detail and correction log |
| GET | /api/dashboard/overview | common filters | scope/basis, KPIs, category counts, uncategorized count |
| GET | /api/dashboard/trends | common filters + interval day/week/month | scope/basis, points, missing_event_time |
| GET | /api/systems | common filters | system counts, shares and category counts |
| GET | /api/models/info | none | runtime mode/status, last successful version, stored versions, optional source report |

Common filters: `data_scope=real|demo` (default real), `source=text|csv`, `system` (or `__unknown__`), `date_from`, `date_to`, `time_basis=event|import`. All dates are interpreted at Riyadh day boundaries. Invalid input is 422, missing record 404, oversize file 413. Validation errors do not echo raw rejected input. Text search escapes wildcard characters and uses parameterized SQLAlchemy statements.

Review is an atomic full review submission, not a sparse patch: all classification/system fields are provided. Setting is_complaint=false clears the effective category in the same transaction. No-op submissions do not duplicate correction history. Current aggregate queries use the effective fields and never count audit rows as extra messages.

## Provenance and persistence

- All Mock results are Demo regardless of client flags.
- Explicit synthetic-input flags and reserved `DEMO-` source IDs force Demo even with a Real predictor. These are application provenance controls, not modifications to the predictor contract.
- The demo sample has no invented publication dates. Imported-at timestamps describe actual insertion only.
- Identical source IDs within the same source/system/scope are deduplicated; different IDs remain independent. Without IDs, exact redacted content and fixed context are the fallback. No fuzzy deduplication.
- Original model scores stay in original_prediction and are labelled as original scores in the UI; never presented as calibrated probabilities or measured accuracy.
- Stored original system_evidence records initial provenance. system_reviewed=true indicates the effective system_name came from a correction; original_system_name remains unchanged.

SQLite is located in backend/storage, consistent with the updated frontend/backend split. No ORM migration tool was added. Initial schema is created non-destructively. PostgreSQL support is a design provision only: actual migration and testing remain deferred.

## Verification record

Final automated verification: 34 passing Pytest cases, 8 passing Vitest cases, and a passing TypeScript/Vite production build. Native Chrome was used for desktop end-to-end analysis/import/reimport/review and 390×844 responsive checks. See PROGRESS.md for chronological evidence. No model-quality result is claimed.

## Remaining integration work owned jointly with model delivery

1. Confirm Claude's real artifacts and compatible dependencies are available.
2. In the same Python environment, invoke real AUTH/PERF/noncomplaint/mixed text cases and verify their actual returned contract (not expected accuracy).
3. Start APP_ML_MODE=real and check analyze/import/persistence/review against the real adapter.
4. Provide an evaluation source report with its exact model_version if the Model Information page should display it.

No request has been sent to Claude or any external service. No training, relabeling research data, OCR, EML, clustering, NER or paid APIs were introduced.

## Bilingual UI and analytical additions

The user subsequently authorized a visual/analytics refinement and English browsing. Language is local to React, persisted as `marsad.language`; all six pages and shared controls switch Arabic/English with RTL/LTR. Arabic complaint text, system names, category labels and analytical numerals are retained. There is no translation service or ML contract change.

Additive `/api/dashboard/overview` response fields:

- `no_review_required_messages`: effective needs_review=false; does not assert independent human review.
- `known_system_complaints`: complaint records with a current non-null system name.
- `dated_complaints`: complaint records with an original event timestamp.
- `sources`: per-source message and complaint counts within current filters.
- `comparison`: null unless both date bounds exist; preceding equal-length period with the same scope/source/system/time basis, current/previous complaint counts, delta, and nullable relative change (null when prior count is zero).

No database migration. Existing response fields and the frozen six-field predictor contract are unchanged. Matrix and dashboard links initialize Explorer filters through URL parameters. Both scopes remain isolated in every aggregate/comparison. Source reports and model errors are not machine translated.
