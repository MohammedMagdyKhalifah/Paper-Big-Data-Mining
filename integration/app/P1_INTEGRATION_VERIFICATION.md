# P1 integration verification — implementation checkpoint, host acceptance pending

Date: 2026-10-31. Checkout: `Project/integration/`, branch `integration/p1`, from verified A4 environment `3b2c2cf`. Claude P1 `d8ffad4` was merged via unsquashed subtree (`afd3bde`). Source agent repositories and branches were preserved. Integrated tracked `ml/` equals Claude's source tree; `ml.infer`, A4 export/pins, training code and evaluation results have no application-authored changes. No retraining or holdout evaluation was run.

**P1 is implemented and partially verified, not fully accepted.** The application/API tests below pass with actual local EasyOCR and MARBERT. Actual browser/localhost execution is blocked in this agent environment, and the unchanged Vision-specific ML tests fail for the documented sandbox restriction. Neither is counted as a success.

## Implemented and verified

- Existing text form uses the real exported P1 wrapper in Real mode; explicit Mock retains its original P0 flow and Demo exclusion. CSV ingestion remains P0, with no email/EML work.
- Screenshot flow: file selection → local preview → explicit extraction → view original/redacted OCR → edit OCR/add description → separate confirmation → real analysis/save. Uploading/extracting does not classify or insert a complaint.
- Typed P1 schemas, server-owned UUID OCR drafts, 24h expiry, upload/pixel/text/backlog limits and explicit validation/deployment errors. Missing/corrupt local fallback weights are rejected before EasyOCR can download them. Extreme image dimensions are rejected before engine loading, including Pillow's decompression-bomb exception (app-boundary fix; ML decoder unchanged).
- Actual `ml.analyze.analyze` output persisted atomically beside the original six-field prediction. Original OCR, correction, exact redacted model input, all system spans, signals, model/engine versions and timing are retained; an OCR correction also creates an audit entry. Review changes effective fields without altering original P1 evidence. No raw image is persisted.
- Identified/ambiguous/unknown systems remain distinct. No guessed primary for multiple mentions. Mention extraction is a registry rule, not a diagnosis of a failing system.
- Source=image filter and source-count labels added to the existing dashboard/explorer. Real/demo separation and missing original dates remain intact. No model metric was fabricated or pooled across datasets.
- Bilingual controls and RTL/LTR preserved; generated counts/scores/offsets use English digits. Existing Arabic source/model content stays intact. Formatting helpers were shared without a component import cycle.

## Tests executed

Commands run from `integration/`, using physically installed `.venv-p1`, without Python path overrides:

| Check | Actual result |
|---|---|
| Final Backend: `ML_OCR_ENGINE=easyocr ML_EASYOCR_CANVAS=1600 app/backend/.venv-p1/bin/python -E -s -m pytest -c app/backend/pytest.ini app/backend/tests -q` | **93 passed**, no skips, 33.35s; includes 64 existing +29 new P1 cases |
| Full Backend+ML attempt (before the final extra oversized-image case) | **233 passed /14 failed**, no skips, 42.81s; every failure is an unchanged ML test explicitly executing Vision |
| ML component of that full run | **141 passed /14 failed**, total155. No assertions or source fixtures were altered to hide these failures |
| `npm --prefix app/frontend test` | **26 passed**, 2 files, 1.96s, no unhandled errors (18 existing +8 new P1) |
| `npm --prefix app/frontend run build` | TypeScript and Vite production build passed; final build236ms with warm dependencies |
| Isolated P1 audit | **77 pinned local distributions**, 25 critical modules, pip check clean, 10 V1/A4 assets +2 EasyOCR assets verified, no external site-packages/Python path overrides |
| Original A4 export SHA256SUMS | All **6/6** entries OK, including ignored safetensors |
| Additive DB upgrade on a backup of the normal DB | Existing complaints/corrections SQL schemas **and every row unchanged**; only `p1_analyses` and `ocr_drafts` added; nine legacy Demo messages preserved |

Backend coverage includes real Arabic complaints, mixed Arabic-English, praise/noncomplaints, unknown/ambiguous/multiple systems and valid evidence offsets, strict schema/prediction identity, invalid/empty/oversized input, malformed/empty/unsupported images, extreme image dimensions, absent/expired drafts, missing OCR assets, engine/model errors, no-text/no-fake-prediction behavior, repeated uploads, demo/real exclusion, review audit, original OCR correction, restart persistence and missing publication dates. Existing CSV/reimport, A4/V1 rollback, report identity, offline startup and model-asset tests pass in the same runtime. A real P1 restart/OCR/model/persistence test blocks Python socket connections; no external inference API is used.

Frontend tests use API doubles for interaction checks; they are **not** browser-to-model acceptance. P1 UI fixture is a recorded actual EasyOCR+unchanged A4 output on Claude's synthetic err00.png, with complete fields; it is not an accuracy measurement. Tests cover manual confirmation, preview, edited payload, context/demo flag, stale-image invalidation, explicit OCR failure, deleted/empty text, pending buttons, English labels/Arabic content and ambiguous-name presentation.

Initial Vitest worker startup timed out; subsequent runs warmed the local dependency files. A pre-existing lazy-dashboard test also raced the asynchronous model query/import: it now waits for the actual route heading before checking the same scope assertions, with a bounded route-load timeout. Default `npm test` now passes. An attempted isolated npm-ci diagnostic under `/private/tmp` failed with registry ENOTFOUND and was never used as the verification environment. Original dependency directories/symlink were preserved.

The optional re-audit of the preserved old .venv-a4-standalone stalled while reading pandas source and was interrupted; it is not counted as a new successful old-environment audit. Its pins/distribution locations passed pre-import checks, and no dependency replacement was made. The selected P1 environment audit and actual A4/V1 executions did pass.

Known warnings: existing Starlette/AnyIO deprecation; pinned EasyOCR/PyTorch quantization deprecations and CPU pin_memory warning. No runtime/model pin changes were made to suppress them.

## Synthetic and published screenshots

Claude's fixtures were used for Arabic error screens, degraded JPEG complaints and no-text/corrupt/unsupported cases. Their synthetic origin is retained; Claude's synthetic CER/WER are not republished as real screenshot accuracy.

Three additional images were fetched from the official [Absher App Store listing, published by NATIONAL INFORMATION CENTER](https://apps.apple.com/sa/app/absher-%D8%A3%D8%A8%D8%B4%D8%B1/id1004966456) via its public Apple metadata. These are published UI screenshots / promotional compositions, **not private field complaints, a representative screenshot dataset, or human OCR gold**. Source URLs/hashes/engine/observed results are in `P1_SCREENSHOT_OBSERVATIONS.json`. The images and full redacted results are ignored local verification artifacts under `backend/storage/p1-recovery/published-screenshots/`.

All3 passed actual upload → EasyOCR → MARBERT → system matching → SQLite APIs (in process), and all were explicitly Demo. Observations:

- Published phone composition,392×696: noncomplaint, Absher identified from English text. Small Arabic text was garbled/truncated.
- Published welcome screen,576×768: noncomplaint, system unknown; scenery, logo text and small controls produced substantial garbling.
- Published services screen,576×768: **classified as complaint** although the image visibly shows a services page; system unknown. This is an observed undesirable result on noisy OCR, not a correct-label claim or a patched model rule.
- OCR durations in that probe were4.2864s,4.3425s,10.1305s respectively; machine/load/canvas-specific observations, not an SLA. Some confidence scores were low; correction remains explicit for every image regardless of score.

These probes show why human OCR review and context are necessary. No CER/WER, recall, accuracy or real-complaint success rate was measured. Real Arabic field complaint captures remain untested because none were available; do not equate these public product images with that coverage.

## Exact execution blockers

1. Apple Vision initializes and reports Arabic support on macOS27.0.1, but executing a recognition request returns `failed / engine_error: Vision request failed: None`. Claude documents the same sandbox behavior. Fourteen unchanged ML tests explicitly require real Vision execution, so they remain failing here even when application fallback is EasyOCR.
2. `npm --prefix app run start` successfully loads real A4, then Uvicorn cannot bind `127.0.0.1:18174`: `Errno1 / operation not permitted`. The same result occurred from the shell and the Node runtime. No local preview is claimed running.
3. Native/browser automation reports `Sky Computer Use native pipe startup failed` and `The browser access host is unavailable`. A separate headless installed-Chrome launch also exited before a page could open. No actual React-browser→HTTP→OCR→model acceptance or visual desktop/mobile QA was possible.

No permission bypass, altered ML test, mock substitution or unmeasured success is used to conceal these limitations. Current local `.env` selects the verified `.venv-p1`, A4 and explicit EasyOCR/canvas1600 fallback; the temporary DATABASE_URL was removed. The stable A4 runtime/settings backup and all original agent work are preserved.

## Remaining acceptance on an ordinary supported local host

1. Start `npm --prefix app run start` from integration/; verify FastAPI and React ports are reachable. Use a separate verification SQLite via DATABASE_URL to keep production data clean.
2. With ML_OCR_ENGINE unset, verify actual Vision extraction and run all155 unchanged ML tests plus Backend tests. If the OS lacks Arabic Vision or service permissions, document that host limitation and explicitly select the supported EasyOCR fallback; never falsify Vision results.
3. In a real browser, test Arabic text, mixed text, praise, unknown/ambiguous/multiple systems, PNG and degraded JPEG preview/extract/edit/confirm. Inspect saved model version/scores/evidence, review correction, Explorer and dashboard filters, missing original dates, repeated image/CSV submissions and restart persistence. Test Arabic/English and desktop/mobile layout. Use Demo for verification probes.
4. Also test genuine field screenshots with known provenance if available; record OCR errors and context without an accuracy claim unless a real reference set is independently labelled.
5. Verify model rollback by removing ML_ARTIFACT_DIR/restarting, preserve prior A4 rows, re-enable A4/restart, then record browser evidence and commit that acceptance checkpoint. Until then M10 stays IN_PROGRESS with host verification BLOCKED.
