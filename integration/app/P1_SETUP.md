# Local P1 setup and integration contract

Run commands from `Project/integration/`, branch `integration/p1`. Application changes are in `app/`; `ml/` is the exact Claude P1 `d8ffad4` subtree. A4 inference, export, training, evaluation and dependency pins are unchanged. Stable application/environment checkpoint: `integration/a4-environment` at `3b2c2cf`; stable MARBERT integration: `integration/a4-marbert`; V1: `integration/real-ml`.

## Install without changing the stable environment

Verified target: CPython 3.12.7, macOS ARM64, CPU, Node 22.20.0. Apple Vision additionally needs an OS version whose Vision framework supports `ar-SA` (verified installed OS: macOS 27.0.1). The wheel lock is platform-specific; do not claim it is a Linux/Windows lock.

```bash
unset PYTHONPATH PYTHONHOME
python3.12 -m venv app/backend/.venv-p1
# Apple Vision runtime: 66 pinned packages, including all original A4 pins.
app/backend/.venv-p1/bin/python -I -m pip install --require-hashes --only-binary=:all: -r app/backend/requirements-p1-macos-arm64-py312.lock
# Optional documented EasyOCR fallback: 77 packages, same A4 pins.
app/backend/.venv-p1/bin/python -I -m pip install --require-hashes --only-binary=:all: -r app/backend/requirements-p1-easyocr-macos-arm64-py312.lock
npm --prefix app/frontend ci
cp -n app/.env.example app/.env
```

Keep `backend/.venv-a4-standalone` and its lock/cache intact. Do not copy site-packages, add `.pth` links, use `--system-site-packages`, or set Python path overrides. Manifests record the selected official PyPI wheels and SHA256. Installation needs network or an already verified wheel cache; inference does not.

Offline installation on this verified machine:

```bash
app/backend/.venv-p1/bin/python -I -m pip install --no-index --find-links app/backend/.wheelhouse-a4 --find-links app/backend/.wheelhouse-p1 --require-hashes --only-binary=:all: -r app/backend/requirements-p1-easyocr-macos-arm64-py312.lock
```

The ignored wheel caches are optional installation assets, not runtime dependencies or Git deliverables.

## Model and OCR assets

Transfer the ignored V1 joblib files and A4 `model/model.safetensors` exactly as documented in `ENVIRONMENT_SETUP.md`. Preserve both versions. Verify `MODEL_ASSETS.json`, `A4_MODEL_ASSETS.json` and the export's original `SHA256SUMS`. No retraining or holdout rerun.

Apple Vision uses on-device OS recognition; no separate OCR weights are required. In this task's sandbox, recognition returns `engine_error` despite successful framework initialization. Supported normal macOS execution must be tested separately; the application does not silently replace failures with fabricated text or switch engines.

For EasyOCR, explicitly transfer these ignored files from Claude's P1 worktree or fetch them once using Claude's documented model-fetch process, then verify the hashes in `P1_OCR_ASSETS.json`:

- `ml/artifacts/ocr/easyocr/arabic.pth`
- `ml/artifacts/ocr/easyocr/craft_mlt_25k.pth`

Both local models were explicitly copied and verified during this integration. The application checks them **before initializing EasyOCR** and refuses missing/corrupt assets, preventing automatic model downloads. EasyOCR is CPU-only here and can require roughly 6–8GB RAM for large screenshots; use `ML_EASYOCR_CANVAS=1600` for the documented lower-memory configuration. It is substantially less reliable than Vision on Claude's synthetic set; those results do not measure real screenshot accuracy.

Tesseract remains an optional ML-supported fallback: install its native binary separately and transfer `ara.traineddata` / `eng.traineddata` to `ml/artifacts/ocr/tessdata/`, checking the same receipt. It is not the selected application fallback, and its screenshot quality is limited. Paddle is not installed in the project environment because of its documented NumPy conflict.

```bash
app/backend/.venv-p1/bin/python -I app/backend/verify_a4_environment.py --profile p1
# With EasyOCR installed and local weights available:
app/backend/.venv-p1/bin/python -I app/backend/verify_a4_environment.py --profile p1-easyocr
```

## Configure and run

`app/.env` paths: APP_PYTHON is relative to `app/`; ML_ARTIFACT_DIR is relative to `integration/`. Caller environment overrides `.env`.

```dotenv
APP_PYTHON=backend/.venv-p1/bin/python
APP_ML_MODE=real
ML_ARTIFACT_DIR=ml/artifacts/a4/export/a4-marbert-v1
HF_HUB_OFFLINE=1
TOKENIZERS_PARALLELISM=false
# Default on supported macOS is Apple Vision; omit ML_OCR_ENGINE for that.
# Explicit fallback only, with packages and local OCR weights installed:
# ML_OCR_ENGINE=easyocr
# ML_EASYOCR_CANVAS=1600
```

```bash
npm --prefix app run start
```

Default ports: React `5173`, FastAPI `8000`; local integration settings retain `15174` / `18174`. Frontend uses the existing Vite `/api` proxy. To start separately, export the `.env` settings in your shell (do not set PYTHONPATH), then run:

```bash
app/backend/.venv-p1/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 18174
# Separate terminal with APP_API_PORT=18174 APP_WEB_PORT=15174 exported:
npm --prefix app/frontend run dev -- --host 127.0.0.1
```

The current agent environment denies localhost sockets (`EPERM`) and browser/native access. A4 loads successfully before the bind fails. This is an outstanding host/browser verification blocker, not a successful launch claim. See `P1_INTEGRATION_VERIFICATION.md` and `SESSION_HANDOFF.md` for the exact remaining acceptance steps.

## Additive REST contract

Existing P0 endpoints and `ml.infer.predict_text`'s exact six keys stay intact. Existing complaint responses have one additive nullable `p1_analysis` field; historical rows return null. Full new response definitions are in `backend/p1_schemas.py`, exposed by OpenAPI.

1. `POST /api/ocr/extract`: multipart `file` (PNG/JPG/JPEG, <=10MB, decoded <=40MP). Returns `{draft_id, expires_at, ocr}`. Extracts only; does not classify or create a complaint. Original images are never persisted. OCR text/lines are redacted using the existing email/phone/ID policy before returning/storing. Engine scores are not calibrated accuracy.
2. `POST /api/complaints/analyze-p1`: JSON with `text` (optional for image flow), `draft_id` (optional for direct text), `corrected_text` (optional nonblank replacement, only with draft), existing metadata/date/demo fields. Browser sends only a server-owned draft token, never a forged OCR dictionary or filesystem path. The combined text must be <=20000 characters.
3. Returns `{message, duplicate, analysis}`. `analysis` validates the exported `p1-analysis-v1` structure; `analysis.prediction` is the unchanged six-field contract. No usable text returns `message=null`, `prediction=null` and no complaint insert. A blank explicit correction is rejected rather than silently restoring the old OCR text.
4. Original OCR, edited OCR, exact redacted classified text, original prediction, rule matches/spans, signals, engine, model version and timing are stored together atomically. OCR edits also create an `ocr_text` correction entry. Existing review PATCH changes only effective classification/system fields; original pipeline evidence remains immutable.
5. Unknown names remain unknown; ambiguous names are displayed for human confirmation. Exactly one confirmed mention populates the existing aggregate system field. Multiple confirmed mentions remain in evidence, with no guessed primary system. Source-app metadata is retained separately and does not prove a P1 text detection. System mentions do not diagnose which system failed.
6. Re-uploading the same image and submitting identical text/correction/context/model deduplicates. Different correction, context or model version is a distinct analysis. OCR draft timing is excluded from the fingerprint. Drafts expire after24h; max100 unexpired drafts; expired drafts are purged on the next extraction.
7. HTTP422: invalid/empty input, unreadable/unsupported image or excessive combined text. HTTP413: upload/OCR text too large. HTTP404/410: missing/expired OCR draft. HTTP429: local draft limit. HTTP503: engine/model unavailable or engine execution failure. No silent Mock fallback. Explicit Mock mode preserves the P0 text/CSV flow; P1 endpoints refuse it.

## Database and rollback

Startup adds `ocr_drafts` and `p1_analyses` using SQLAlchemy `create_all`. No existing complaint/correction columns, rows, scores or original timestamps are rewritten. This additive upgrade was tested on a backup of the original nine Demo rows. Back up your SQLite before first startup. P1 results use source `image` or `text`; missing original dates remain null, separate from import time. All synthetic/public smoke probes are Demo and excluded from Real analytics.

V1 model rollback: remove `ML_ARTIFACT_DIR` from `.env` and caller environment, restart using the same `.venv-p1`. Re-add the A4 path/restart to return. Process-local model caching requires restart. No stored results are reclassified or overwritten.

Exact stable application rollback: with clean committed work, switch to `integration/a4-environment` and select the original standalone A4 interpreter/settings. The ignored backup `backend/storage/p1-recovery/stable-a4.env` preserves the previous local setup. Extra P1 tables are harmless to the old application; do not drop them or delete either model. Historical environment instructions remain in `ENVIRONMENT_SETUP.md`.

## Verification

```bash
# Current sandbox-compatible actual Backend acceptance:
ML_OCR_ENGINE=easyocr ML_EASYOCR_CANVAS=1600 app/backend/.venv-p1/bin/python -E -s -m pytest -c app/backend/pytest.ini app/backend/tests -q
npm --prefix app/frontend test
npm --prefix app/frontend run build
# Full unchanged ML suite, on a host where Apple Vision executes successfully:
app/backend/.venv-p1/bin/python -E -s -m pytest -c app/backend/pytest.ini app/backend/tests ml/tests -q
```

The full ML suite explicitly selects Vision in14 tests; setting ML_OCR_ENGINE=easyocr does not reroute them. They currently fail in this sandbox and must be rerun on the supported normal host, without changing their assertions or replacing OCR. Do not report full acceptance until actual browser + host Vision verification succeeds. Email ingestion, EML, clustering, model training and evaluation reruns are excluded.
