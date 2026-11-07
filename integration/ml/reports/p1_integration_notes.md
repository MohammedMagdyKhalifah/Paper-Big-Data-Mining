# P1 Integration Handoff (for Codex / `app/`): text + screenshot analysis

Branch `agent/claude-ml-p1` (worktree `ml/.worktrees/p1/ml`) is built on `agent/claude-ml-a4`. It changes nothing in `app/`,
in the stable branch, in A4 artifacts or in `ml.infer`. Evidence for everything below is in `reports/p1_report.md`.

## 1. Contract

`ml.infer.predict_text(text) -> dict` is **unchanged**: the same six keys, the same errors, and the trained model only. P1
adds a separate structure around it.

```python
from ml.analyze import analyze, extract_text, warmup        # all local/offline

warmup() -> {"model_version", "ocr_engine", "elapsed_s"}    # call once at FastAPI startup (cold load up to ~20 s)

analyze(text: str | None = None,          # the user's typed complaint
        image: str | Path | bytes | PIL.Image | None = None,   # PNG/JPEG screenshot -> OCR'd here
        *, image_ocr: dict | None = None,  # OR a previous extract_text() result (two-step correction flow)
        corrected_text: str | None = None, # user-corrected OCR text; replaces OCR text for classification
        ocr_engine: str | None = None)     # "vision" | "easyocr" | "tesseract"; default per platform / ML_OCR_ENGINE
     -> dict  (schema "p1-analysis-v1", below)

extract_text(image, *, engine=None) -> dict   # OCR only (to show the text to the user before classifying)
from ml.src.systems import find_systems       # find_systems(text) -> dict (system detection only)
```

Errors:
* `ValueError`: nothing usable was given (no text, image or corrected text), or both `image` and `image_ocr` were given.
* `TypeError`: wrong argument types.
* `OCRUnavailableError` (from `ml.src.ocr`): the OCR engine is not installed. This is a deployment error; return a 503, not an empty result.
* `FileNotFoundError`: the model artifacts are missing (from `predict_text`).
* A **bad image never raises**. It is reported as `ocr.status = "failed"` with an error code.

Two-step flow, recommended when the app lets users correct OCR:
1. Call `ocr = extract_text(upload)` and show `ocr["text"]`, plus a warning when `ocr["low_confidence"]` is true.
2. Call `analyze(text=user_text_or_None, image_ocr=ocr, corrected_text=edited_or_None)`.

One-step flow: `analyze(text=..., image=upload)`.

## 2. Result schema `p1-analysis-v1`

| key | meaning |
|---|---|
| `schema_version` | `"p1-analysis-v1"` |
| `analysis_kind` | `complaint` / `not_complaint` (from the model) · `error_screen_signal` (see below) · `no_text` (no readable text) · `ocr_failed` (image unusable, no typed text) |
| `input` | `has_user_text`, `has_image`, `text_source` ∈ {`user_text`, `ocr`, `ocr_corrected`, `user_text+ocr`, `user_text+ocr_corrected`, null}, `classified_text` (exactly what was sent to the model: user text, then a newline, then image text) |
| `prediction` | **`predict_text(classified_text)` verbatim** (six keys), or `null` if nothing was classified |
| `systems` | `find_systems(classified_text)` or `null`: `status` ∈ {`identified`, `ambiguous`, `unknown`}; `systems[]` = {`system_id`, `name_ar`, `name_en`, `mentions[]` = {`text`, `start`, `end`, `basis`}}; `possible_mentions[]` (an ambiguous name without context: **not identified**, can be shown for user confirmation); `generic_references[]` ("التطبيق"…); `registry_version`; `method` |
| `signals` | `error_message_cues[]` {`text`, `start`, `end`, `cue`}; `narrative_markers[]`; `needs_user_context` (true only for `error_screen_signal`); `ocr_needs_review` (low OCR confidence) |
| `ocr` | `null` for text-only input; otherwise `extract_text` output: `status` ∈ {`ok`, `empty`, `failed`}, `text`, `lines[]` {`text`, `confidence`, `bbox`}, `mean_confidence`, `low_confidence`, `error` {`code` ∈ `unsupported_format` / `unreadable_image` / `file_not_found` / `engine_error`, `message`}, `engine`, `image` {`format`, `width`, `height`}, `elapsed_ms`, plus `corrected_text` and `used_for_classification` |
| `notes[]` | human-readable explanations (English) |
| `timing_ms` | `ocr_ms`, `classify_ms`, `systems_ms`, `total_ms` |

All spans (`start`, `end`) index into `input.classified_text`, and `classified_text[start:end] == text`.

`error_screen_signal` means: an image-only input whose OCR text contains an error-message cue and no first-person/narrative
marker. The **model prediction is still attached**, but the screen alone does not describe the user's problem, so the UI
should ask for context. It is a lexical signal, **not a diagnosis**.

Do not present `systems` as "the system that failed". It lists names the text mentions.

## 3. Sample inputs / outputs

These are recorded with `a4-marbert-v1` and Apple Vision in `tests/fixtures/p1/sample_outputs.json` (17 scenarios), with
the images alongside. Excerpts:

```text
analyze(text="الـ OTP ما يوصلني when I try to login في تطبيق Absher")
 -> analysis_kind "complaint"; prediction {is_complaint: true, complaint_score: 0.9876, category: "AUTH",
    category_score: 0.9072, needs_review: false, model_version: "a4-marbert-v1"};
    systems.status "identified": absher, mention "Absher" [47:53], basis "registered_alias"

analyze(image="tests/fixtures/p1/err00.png")        # error dialog under an app bar "أبشر"
 -> analysis_kind "error_screen_signal", signals.needs_user_context true,
    error_message_cues ["حدث خطأ", "عذرا", "حدث خطأ", "يرجى المحاولة", "رمز الخطأ"],
    prediction {is_complaint: true, category: "TRANS", category_score: 0.4085, needs_review: true},
    systems.status "ambiguous" (possible_mentions: absher "أبشر" [0:4]), ocr.status "ok"

analyze(image="tests/fixtures/p1/notext0.png") -> "no_text", prediction null
analyze(image="tests/fixtures/p1/corrupt.png") -> "ocr_failed", ocr.error.code "unreadable_image"
analyze(image="tests/fixtures/p1/tiny.gif")    -> "ocr_failed", ocr.error.code "unsupported_format"
```

## 4. Dependencies and setup

Python 3.12; the same environment as the A4 MARBERT model.

```bash
pip install -r ml/requirements-p1.txt            # A4 inference set + pillow + pyobjc Vision (macOS only)
# optional portable OCR (non-macOS default):  pip install -r ml/requirements-p1-easyocr.txt
#                                              bash ml/scripts/p1_fetch_ocr_models.sh --easyocr
export ML_ARTIFACT_DIR=/abs/path/ml/artifacts/a4/export/a4-marbert-v1   # use MARBERT (else the v1 TF-IDF default)
export HF_HUB_OFFLINE=1
```

* **OCR default**: Apple Vision on macOS (on-device, no download). On other systems the default is EasyOCR (285 MB models,
  ~6–8 GB peak RAM). Override with `ML_OCR_ENGINE`.
* **Model weights**: `a4-marbert-v1/model/model.safetensors` (328 MB) is gitignored. Copy it, then verify it with
  `shasum -a 256 -c SHA256SUMS` (see `reports/a4_integration_notes.md`).
* **Registry**: `ml/configs/systems.yaml`. To add systems, edit the YAML or set `ML_SYSTEMS_REGISTRY=/path/other.yaml`.
  No retraining is needed. Restart the process to reload, since the registry is cached.
* **Error cues**: `ml/configs/error_cues.yaml`.
* **Thread-safety**: the model, OCR engine and registry are loaded once per process, under locks. Apple Vision requests are
  per call. CPU inference: run `analyze` in a threadpool (`run_in_threadpool`), not on the event loop.
* **Uploads**: only PNG/JPEG are accepted; images over 40 MP are rejected (`unreadable_image`). Cap the upload size in FastAPI as well.

**Vision in sandboxes:** in Codex's sandboxed run, Apple Vision initialised but every request failed (`ocr.status="failed"`, `error.code="engine_error"`). Check on the deployment host with `extract_text("ml/tests/fixtures/p1/err00.png")`; if it fails, set `ML_OCR_ENGINE=easyocr` (or tesseract).

## 5. Performance (M2 Max CPU, one process with Vision + MARBERT)

| | |
|---|---|
| per screenshot | p50 134 ms (OCR 104, classify 32, systems 0.2) |
| warm-up | 3.8 s warm cache, ~19 s cold |
| memory | peak RSS 1.56 GB |

With EasyOCR instead of Vision: +1.9–3.3 s per image and +5–7 GB peak.

## 6. Tests

```bash
cd ml/.worktrees/p1/ml && HF_HUB_OFFLINE=1 .venv/bin/pytest -q
```
155 tests pass (2026-10-31): contract, A4, and P1 OCR, systems and analyze tests (P1 tests written by Codex). P1 tests skip when a platform engine or the
MARBERT weights are unavailable.

## 7. Out of scope / open owner decisions
* Not included: email/EML ingestion, mailboxes, OCR training, NER fine-tuning.
* Promotion of `a4-marbert-v1` as the default model is still the owner's decision (`reports/a4_integration_notes.md`).
* The owner should check the OCR on a few **real** screenshots; the evaluation is synthetic only. Put them in
  `ml/data/ocr_eval/real/` with a `manifest.jsonl` in the same format and run `scripts/p1_ocr_run.py --set real` and
  `p1_ocr_eval.py --set real`.
