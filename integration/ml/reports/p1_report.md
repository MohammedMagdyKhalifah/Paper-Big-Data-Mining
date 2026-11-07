# P1: Arabic Text & Screenshot Analysis (OCR, System Names, Unified Pipeline)

Branch `agent/claude-ml-p1` (worktree `ml/.worktrees/p1/ml`), based on A4 (`a4-marbert-v1`). There was **no retraining and
no holdout evaluation**: MARBERT is used as exported, through the unchanged `ml.infer.predict_text` contract. Every number
here comes from a file under `results/p1/`, and the commands are listed at the end.

**Provenance caveats (read first)**
* The OCR set is **synthetic**: HTML screens rendered by headless Chrome, with the reference = the exact DOM text. **No real
  screenshots were available**, so `data/ocr_eval/real/` is empty and nothing is reported for it. Real-screenshot CER is unknown.
* The system-mention reference labels are **AI-assisted** (sonnet + fable coders, opus adjudicator, all blind). They are **not human gold**.
* The error-screen lexicon and the narrative-marker rule were written by hand. The narrative rule was added after looking at
  the synthetic set, so the synthetic analysis-kind numbers are development numbers. The independent check is on real AURA
  texts (§3.3).

## 1. P1.1 OCR: engine comparison (synthetic set, 64 images)

Contents of the set (`scripts/p1_make_ocr_eval.py`, seed 31):
* 12 hand-written error screens (Arabic and English).
* 6 hand-written chat complaints (mixed Arabic-English, system names, negation/past).
* 12 real AURA review texts (A4 train split).
* 2 images without text (gradient + star icons).

Each screen comes in two variants: a clean PNG (1000×2000 px) and a degraded copy (×0.6, JPEG q=55, like a forwarded
screenshot). Fonts are SF Arabic, Geeza Pro and Arial; light and dark themes.

CER/WER are micro-averaged over the 60 text images. *light* = NFKC, digits, no diacritics/tatweel, whitespace collapsed, and
reading order kept. *letters* = light + alif/ya/ta-marbuta folding, no punctuation.
(`results/p1/ocr_metrics_synthetic.json`)

| engine | CER light | WER light | CER letters | WER letters | no-text → "empty" | p50 latency | peak RSS | notes |
|---|---|---|---|---|---|---|---|---|
| **Apple Vision** (macOS 27.0.1, ar-SA+en-US, accurate) | **0.0021** | **0.0163** | **0.0004** | **0.0032** | 4/4 | **124 ms** | **0.32 GB** | on-device; macOS only |
| EasyOCR 1.7.2 (ar+en, canvas 1600) | 0.0338 | 0.1508 | 0.0199 | 0.0768 | 4/4 | 1.86 s | 6.35 GB | portable; same torch stack |
| EasyOCR 1.7.2 (default canvas 2560) | 0.0351 | 0.1508 | 0.0215 | 0.0801 | 4/4 | 3.32 s | 8.10 GB | |
| PaddleOCR 3.7.0 (lang=ar, PP-OCRv5 arabic rec) | 0.0482 | 0.1247 | 0.0352 | 0.0866 | 4/4 | 8.61 s | 12.6 GB | needs numpy 2.3.5 (A4 pins 2.5.4) → separate venv |
| Tesseract 5.5.2 (tessdata_best ara+eng) | 0.3458 | 0.3623 | 0.3435 | 0.3550 | 0/4 | 277 ms | 0.19 + 0.16 GB | misses text in coloured bubbles (chat CER 0.67) |

Clean vs degraded CER (light): Vision 0.0012 / 0.0031; EasyOCR-1600 0.0258 / 0.0418; Paddle 0.0539 / 0.0425; Tesseract 0.3251 / 0.3665.
Dark vs light theme: Vision 0.0024 / 0.0019. All per-font, per-theme and per-kind tables are in the JSON.

**Decision.** The default engine is **Apple Vision on macOS** (`DEFAULT_ENGINE`). It is the most accurate by an order of magnitude,
the fastest, and the lightest, and it needs no model download. On other platforms the default is **EasyOCR** (portable,
CER 3.4%, but heavy RAM). Tesseract is kept only as a light option and is not recommended for UI screenshots. PaddleOCR
is not supported in the main environment because it conflicts with the pinned numpy; the adapter remains for reproduction
in `.venv-paddle`. The engine can be overridden with `ML_OCR_ENGINE` or `extract_text(..., engine=)`.

What was and was not tuned:
* Engines ran with default settings. The only exceptions were cost or plumbing settings: the EasyOCR detector canvas, and
  Tesseract's grayscale/invert-dark/×2-upscale pre-processing.
* Tesseract's TSV call was fixed once (a config-path bug made every image `failed`); the bug was visible in the metrics.
* One generic rule applies to all engines: a line with no letter or digit (e.g. `*****` read from star icons) is dropped, so
  icon-only images return `empty`.
* No accuracy tuning was done on this set.

**Bias.** The synthetic screens use Apple system fonts rendered by Chrome on macOS, which plausibly favours Apple Vision. Real
Android screenshots, photos of screens, other fonts, small text and busy backgrounds are **not covered**.

Status semantics (`ml.src.ocr.extract_text`):
* `ok`: text found.
* `empty`: the image was read but no readable text was found.
* `failed`: the image could not be used, with `error.code` ∈ {`unsupported_format` (only PNG/JPEG), `unreadable_image`
  (corrupt, 0 bytes, too large), `file_not_found`, `engine_error`}.
* A missing or misconfigured engine raises `OCRUnavailableError`; this is never turned silently into an empty result.

Line confidences are the engine's own scores in [0, 1] and are **not calibrated**. Apple Vision's scores are coarse
(0.3 / 0.5 / 1.0 steps). `low_confidence` (mean < 0.60) is a prompt to show the text to the user for correction.

## 2. P1.2 System-name identification

Method (`ml/src/systems.py`, registry `configs/systems.yaml`): transparent rules, with no learned model and no NER.
* Normalised (alif/ya/ta-marbuta/diacritics/tatweel), word-bounded matching. The proclitics و/ف/ب/ل/ك are allowed.
* Spans are offsets into the original string.
* **Registered aliases** (multi-word names, Latin spellings) are identified directly.
* **Ambiguous names** are names that are also ordinary words (ابشر "sure", صحتي "my health", موعد "appointment"…). They are
  identified only with a context cue in the 3 preceding tokens (تطبيق/منصة/موقع/بوابة/app…) or when quoted. Otherwise they
  are returned as `possible_mentions` and are **not identified**.
* `exclude_after` drops ordinary phrases such as توكلنا على الله.
* Generic references (التطبيق, the app) are reported separately; they never name a system.
* `status` ∈ {identified, ambiguous, unknown}. Nothing is guessed from error messages or topics, and detection does not
  say which system failed or why.
* Registry v1 has 30 Saudi government/public digital services. New systems are added by editing YAML (or pointing
  `ML_SYSTEMS_REGISTRY` to another file), with no retraining.

**Evaluation** (`scripts/p1_mention_sample.py`, `p1_mention_eval.py`).

Registry v1 was **frozen and committed (a3035f4) before** the sample was drawn and labelled. The sample has 339 deduplicated
AURA reviews:
* 239 *name-hit* items, where a registry name occurs as a loose substring (≤12 per system). This enriched stratum measures
  precision and ambiguity.
* 100 *gov-app no-hit* items: random reviews of registry apps without any name substring. This stratum measures missed mentions.

Two blind coders agreed on the system set for 334/339 items (pair-level κ = 0.982); 5 items were adjudicated. The reference
has 145 (item, system) pairs in 125 items. (`results/p1/mention_metrics_registry_v1.json`)

| method (registry v1, unbiased) | precision | recall | F1 | item exact match |
|---|---|---|---|---|
| **rules v1 (shipped)** | **0.958** (91/95) | 0.628 (91/145) | 0.758 | 0.850 |
| ablation: ambiguous names accepted without context | 0.733 | 0.945 | 0.825 | 0.832 |
| naive substring | 0.511 | 0.993 | 0.675 | 0.608 |

* All 54 misses are in the name-hit stratum. The gov-app no-hit stratum (100 reviews) had **no** reference mentions, so no
  misspelling-only misses were observed there.
* **Conservatism at work.** 92 ambiguous names were returned as `possible_mentions`; 46 of them were true mentions according to
  the reference. These account for 46 of the 54 misses. An app can show them for user confirmation; together, identified and
  possible mentions cover 137/145.
* **4 false positives**: "تطبيق وطني" (= "a national app"), "كلنا امن وامان" (a slogan), "سبل الراحة" ("means of comfort",
  matching سبل = SPL), and "تطبيقات بلدي" ("my country's apps").
* **Remaining misses**: unregistered variants (النفاذ, النفاذ الموحد, بوابة النفاذ, تطمنا, عالنفاذ, يااعتمرنا).
* **Registry v1.1 (shipped)** adds النفاذ الموحد / بوابة النفاذ / النفاذ / تطمنا. On the same sample this gives P 0.959,
  R 0.648, F1 0.774, but this is **in-sample and optimistic** (`mention_metrics_registry_v1.1.json`).
* Reviews are not screenshots. The precision/recall above are on an *enriched* review sample and are not population rates.

## 3. P1.3–P1.4 Unified pipeline (`ml.analyze.analyze`) with the real `a4-marbert-v1`

`results/p1/pipeline_eval.json` uses the default engine (Apple Vision) on CPU (M2 Max) in one process.

### 3.1 OCR → classification consistency (synthetic, no labels)
`predict_text(reference text)` vs the prediction from `analyze(image=…)`, over 30 clean and 30 degraded images:
* Same `is_complaint`: 100% / 100%.
* Same category: 100% / 100%.
* Same `needs_review`: 100% / 100%.
* Maximum |Δ complaint_score|: 0.0005 / 0.0008.

With Vision on these screens, OCR noise did not change any decision. This says nothing about real screenshots, where OCR is worse.

### 3.2 Error-screen signal vs model-classified complaint (synthetic, development)
`analysis_kind = error_screen_signal` when: the input is image-only, an error-message cue is present (configs/error_cues.yaml),
and there are **no** first-person/narrative markers. The model prediction is still attached, `signals.needs_user_context = true`,
and the note asks for the user's own description.

| screenshot kind | result |
|---|---|
| error screens | 24/24 error_screen_signal |
| chat complaints | 12/12 complaint |
| reviews | 16 complaint, 6 not_complaint, 2 error_screen_signal (one review, both variants) |
| no-text | 4/4 no_text |

Before the narrative rule, 6/36 user-text screenshots were flagged as error screens. The rule was added to fix this, so these
counts are not an unbiased test.

### 3.3 Error-screen rule on real user texts (independent check)
2,000 random deduplicated AURA reviews were treated as if they were image-only OCR text. Every flag is a false error-screen flag.
* 32 contain an error cue, and 20 of those would be flagged.
* Overall false-flag rate: 1.0%. Among cue-containing texts: 62.5%. Many reviews describe errors in the third person
  ("التطبيق لا يعمل… يعطيك خطأ").
* The consequence is limited (the app asks for context; the classification is unchanged), but the signal is **weak for text that mentions errors**.

### 3.4 Scenario suite (fixtures `tests/fixtures/p1/`, outputs recorded in `sample_outputs.json`)
| scenario | analysis_kind | model (is_complaint, category, needs_review) | systems |
|---|---|---|---|
| Arabic OTP complaint | complaint | True, AUTH, False | unknown |
| praise | not_complaint | False, –, False | unknown |
| mixed Arabic-English + "Absher" | complaint | True, AUTH, False | identified absher |
| negated ("ما فيه أي مشكلة") | not_complaint | False | unknown |
| **historical/resolved** ("كانت عندي مشكلة… انحلت") | complaint | **True, AUTH, needs_review True** | identified sehhaty |
| ordinary words (ابشر، توكلنا على الله) | not_complaint | False | ambiguous (absher possible; توكلنا excluded) |
| unknown system ("تطبيق سهل…") | complaint | True, TRANS, True | unknown |
| multiple systems | complaint | True, AUTH, True | najiz + nafath |
| error screen, image only | error_screen_signal | True, TRANS, True | ambiguous (header "أبشر" alone) |
| same + user text | complaint | True, TRANS, True | ambiguous |
| English error screen | error_screen_signal | True, AVAIL, True | unknown |
| complaint chat screenshot | complaint | True, TRANS, True | ambiguous ("من أبشر" has no cue) |
| degraded JPEG chat | complaint | True, AUTH, False | ambiguous |
| no-text image / corrupt PNG / GIF | no_text / ocr_failed / ocr_failed | – | – |
| OCR corrected by the user | error_screen_signal | True, AUTH, False | identified nafath |

The resolved past problem is **classified as a complaint** by MARBERT (with `needs_review`). This is a model limitation
that is reported, not patched with rules. An app-bar title that is only "أبشر" stays ambiguous by design, since a bare
"ابشر" line in a chat means "sure".

### 3.5 Cost (one process: Vision + MARBERT on CPU)
* `warmup()` (model + OCR + registry): 3.8 s warm cache. The first load after boot was ~19 s. Apple Vision's very first
  Arabic request on this machine took 62 s once (OS asset load); after that the first call in a fresh process took ~0.6 s.
* Per screenshot: OCR p50 104 ms, classification p50 32 ms, system detection 0.2 ms; total p50 134 ms (p95 153).
* Peak RSS 1.56 GB, dominated by MARBERT (fp16 on disk, fp32 in memory). With EasyOCR instead of Vision, add ~5–7 GB peak.

## 4. Limitations
1. No real screenshots, so the OCR numbers are synthetic only, and Vision may be favoured by Apple-rendered fonts.
2. Apple Vision is macOS-only. Its model is part of the OS (on-device per Apple), and its version follows the OS.
   The cross-platform fallback (EasyOCR) is roughly 15× worse in CER and much heavier.
3. Confidences are uncalibrated engine scores.
4. Reading order is rows top→bottom, right→left for Arabic rows. Multi-column layouts and tables can be misordered.
5. System detection covers only the registry (30 gov services). It is conservative: recall 0.63 unbiased, with true mentions
   often left as `possible`. Its labels are AI-assisted, its sample is review text (not screenshots), and it does not cover
   non-gov apps (stc, banks, delivery), which must be added to the registry.
6. The error-screen signal is lexical. It is weak on reviews that describe errors (§3.3), and it never diagnoses a root cause.
7. MARBERT behaviour is unchanged from A4, including its errors on resolved/historical problems.
8. **Apple Vision failed inside Codex's sandboxed test run** (`engine_error: Vision request failed: None`; 14 tests failed there, all 155 pass in a normal session). A sandboxed or headless service may lack Vision access. `extract_text` then reports `failed/engine_error` (no crash); use `ML_OCR_ENGINE=easyocr` in such deployments and verify on the target host.
9. Out of scope (per brief): email/EML ingestion, mailbox integrations, NER fine-tuning, OCR training.

## 5. Reproduce (from `ml/.worktrees/p1/ml`)
```bash
bash scripts/p1_fetch_ocr_models.sh [--easyocr]                       # tessdata (+ EasyOCR models)
PYTHONPATH=.. .venv/bin/python scripts/p1_make_ocr_eval.py            # synthetic screenshots (needs Google Chrome)
for e in vision tesseract easyocr; do PYTHONPATH=.. .venv/bin/python scripts/p1_ocr_run.py --engine $e; done
ML_EASYOCR_CANVAS=1600 PYTHONPATH=.. .venv/bin/python scripts/p1_ocr_run.py --engine easyocr --tag _canvas1600
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True PYTHONPATH=.. .venv-paddle/bin/python scripts/p1_ocr_run.py --engine paddle
PYTHONPATH=.. .venv/bin/python scripts/p1_ocr_eval.py
PYTHONPATH=.. .venv/bin/python scripts/p1_mention_sample.py && PYTHONPATH=.. .venv/bin/python scripts/p1_mention_eval.py
ML_ARTIFACT_DIR=$PWD/artifacts/a4/export/a4-marbert-v1 PYTHONPATH=.. .venv/bin/python scripts/p1_pipeline_eval.py
```
Latency and memory vary with machine load. The mention coders and adjudicator were Claude subagents (workflow runs
wf_ba7b1a56-c15, wf_2aaa4620-c04); their outputs are stored in `data/p1/mentions/`.
