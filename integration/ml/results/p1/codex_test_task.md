# P1 test task

Work is restricted to the three new P1 test modules and this notes file. No production code, configuration, artifacts, fixtures, or existing tests are changed. No commits, training, or evaluation jobs are performed; the requested tests use local inference only.

## Coverage

- `tests/test_p1_ocr.py`: real Vision success/empty results, result schema and confidence bounds, invalid/corrupt/unsupported/missing image errors, argument types, path/bytes/PIL equivalence, optional local Tesseract, engine selection/cache behavior, low-confidence threshold, and explicit CER/WER edit counts. Validation tests use a recognizer that must never be called so they also run without installed OCR engines.
- `tests/test_p1_systems.py`: context-sensitive and registered mentions, exclusions, quoted names, appearance order, overlapping aliases, attached proclitics, Arabic normalization and original-character maps, generic references, unknown/empty/type cases, extensibility from an in-memory registry, duplicate IDs/normalized aliases, and explicit/environment-selected temporary YAML registries. All mention/possible/generic spans are checked against their original input.
- `tests/test_p1_analyze.py`: real MARBERT selection with cache/environment cleanup, exact top-level and unchanged six-key prediction contracts, direct predict_text equality, complaint/praise and screenshot flows, OCR failure fallback, corrected OCR, evidence offsets, input errors, warmup, lexical error/narrative helpers, and every recorded sample scenario using the original fixture inputs.

The analyze module is skipped when its real safetensors export is absent. Real Vision-dependent tests skip on non-macOS or OCRUnavailableError. Tesseract skips when its binary or required local language data are unavailable. Recognizer substitutes are confined to decoder validation, confidence threshold, and engine-selection unit tests; MARBERT predictions and screenshot recognition are real.

## Validation

The targeted command completed with **94 passed, 14 failed, 0 skipped** in **6.89 seconds** (exit status 1):

```sh
HF_HUB_OFFLINE=1 .venv/bin/pytest -q tests/test_p1_ocr.py tests/test_p1_systems.py tests/test_p1_analyze.py
```

Only assertion diagnostic messages were enhanced after that run to expose the OCR error dictionary. The requested **single full-suite run** completed with **141 passed, 14 failed, 0 skipped** in **12.13 seconds** (exit status 1):

```sh
HF_HUB_OFFLINE=1 .venv/bin/pytest -q
```

Bytecode generation and pytest's cache provider were disabled for both commands through `PYTHONDONTWRITEBYTECODE=1` and `PYTEST_ADDOPTS='-p no:cacheprovider'` to avoid creating unrelated repository files. Pytest temporary fixtures remained in the operating system's temporary directory. No additional test commands were run.

| Scope | Total | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: | ---: |
| New OCR tests | 33 | 30 | 3 | 0 |
| New systems tests | 27 | 27 | 0 | 0 |
| New analyze tests | 48 | 37 | 11 | 0 |
| Targeted P1 suite | 108 | 94 | 14 | 0 |
| Existing tests in full suite | 47 | 47 | 0 | 0 |
| Full suite | 155 | 141 | 14 | 0 |

## Failures and bugs

One underlying runtime issue was observed: **Apple Vision initializes successfully but cannot execute recognition in this test environment**. The valid PNG/JPEG fixtures return the following error instead of recognized text or an empty result:

```python
{"status": "failed", "error": {"code": "engine_error", "message": "Vision request failed: None"}}
```

Reproduction is preserved in `test_vision_error_screen_has_text`, which calls `extract_text(FIXTURES / "err00.png", engine="vision")`; `test_blank_image_is_empty` reproduces the same issue using `notext0.png`. In `src/ocr.py`, VisionEngine.run raises RuntimeError when performRequests_error_ returns a false success flag; extract_text converts that to engine_error. The framework supplies no underlying error object here. The tests establish the execution failure, but do not establish whether its root cause is the framework/runtime restrictions or production code. This is not evidence of fourteen independent code bugs.

No production fixes or xfail/skip suppression have been applied. These remain ordinary failing tests because the requested skip conditions (non-macOS or OCRUnavailableError) do not apply: Vision initialization succeeds. The Tesseract smoke test passes on the same error-screen fixture.

### Affected tests

Three OCR failures:

- `test_vision_error_screen_has_text`: err00.png produces failed instead of ok.
- `test_blank_image_is_empty`: notext0.png produces failed instead of empty.
- `test_extract_text_agrees_for_path_bytes_and_pil`: all representations fail recognition before successful text equivalence can be established; their decoded RGB pixels agree in the separate decoder tests.

Five dedicated analyze failures:

- `test_image_only_error_screen_needs_context`: OCR failure produces ocr_failed instead of error_screen_signal.
- `test_error_screen_with_user_text_is_classified_as_narrative`: OCR failure leaves text_source=user_text instead of user_text+ocr. The subsequent evidence-offset assertions are present but are not reached in this environment.
- `test_chat_narrative_is_not_an_error_screen`: chat03.png has failed OCR before its narrative can be inspected.
- `test_blank_image_has_nothing_to_classify`: OCR failure produces ocr_failed instead of no_text.
- `test_two_step_flow_uses_corrected_ocr_text`: the prerequisite real extraction of err03.png fails. The separate recorded corrected-text scenario does pass, demonstrating correction-based classification even when recognition fails.

Six recorded-scenario regressions fail: `error_screen_image_only`, `error_screen_with_user_text`, `english_error_image`, `complaint_chat_image`, `degraded_jpeg_image`, and `no_text_image`. Five have the wrong analysis_kind after OCR failure; `error_screen_with_user_text` retains the expected complaint prediction but systems.status becomes unknown rather than ambiguous because the OCR system mention is missing. The other eleven recorded scenarios pass, including all eight text-only cases, corrupt image, unsupported GIF, and corrected OCR text.

Decoder validation, confidence ranges/thresholds, supported engine selection, Tesseract recognition, CER/WER examples, all system registry cases, real-model six-field prediction equality, corrupt-image fallback, direct error-cue/narrative helpers, argument validation, and warmup all pass. Successful Vision recognition, image-only signals, OCR-derived spans with the prepended-user-text offset, and the positive two-step extraction prerequisite remain unverified because of the preserved runtime failure.

## File ownership and execution scope

Created only `tests/test_p1_ocr.py`, `tests/test_p1_systems.py`, `tests/test_p1_analyze.py`, and this file. The initial untracked files `reports/p1_mention_guide.md`, `requirements-p1-easyocr.txt`, and `requirements-p1.txt` were left untouched. This task did not modify tracked files or source/configuration/artifact/fixture/existing-test files, make git commits, or run model training/evaluation jobs. The full suite includes its existing tiny synthetic contract-test fits; no new training behavior was introduced.

Final read-only git verification also showed changes outside this task's ownership: tracked modifications to `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, and `SESSION_HANDOFF.md`, plus untracked `reports/p1_integration_notes.md` and `reports/p1_report.md`. Those were absent from the initial status, were not written by this task, and were left untouched. All three new test modules passed syntax and trailing-whitespace checks. No full-suite rerun was performed.
