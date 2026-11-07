# Data Manifest

All counts come from `scripts/download_data.py` (`data/raw/provenance.json`) and `scripts/prepare_data.py` (`reports/record_flow.json`).

## Sources

| | AURA-Sentiment | AURA-Classification v2.0 |
|---|---|---|
| Hub id | `irfan-ahmad/AURA-Sentiment` | `irfan-ahmad/AURA-Classification` (config v2.0) |
| Pinned revision | `5e3e345845ba361c2ceb701abf3d53989782485d` | `686a01bab9c9ca45d1605b4aad0cd0a89c3a2286` |
| File | `data/train-00000-of-00001.parquet` | `AURA-Classification-V2.csv` |
| sha256 | `75b6e061…df2db5` | `68cf21cb…11a055` |
| Downloaded (UTC) | 2026-10-29T20:28:54 | 2026-10-29T20:28:55 |
| License | MIT (dataset card: "shared under the MIT License … ensure appropriate attribution") | MIT (same wording) |
| Rows | 29,700 | 2,900 |
| Columns | `review, appName, platform, sentiment` | `review, appName, platform, label` |
| Labels | sentiment: positive 14,850 / negative 14,850 | rating 1,298 / bug_report 756 / improvement_request 442 / others 404 (human annotation) |
| Apps | 294 | 289 (all also present in AURA-Sentiment) |
| Platforms | android 14,850 / ios 14,850 | android / ios |
| **Original date** | **none** | **none** |

Citations (requested by the authors):
- O. Aljeezani, D. Alomari, I. Ahmad, "Arabic App Reviews: Analysis and Classification," *ACM TALLIP*, 24(2), 1–28, 2025.
- D. Alomari, I. Ahmad, "Scarcity to clarity: Unraveling Arabic app reviews with minimal data," *Information Processing & Management*, 2026 (in press). Required for v2.0 labels.

## Scope relative to the proposal
- The proposal targets Saudi e-government apps. AURA covers 294 apps from many domains, so the core sample prioritises the ~45 Saudi government/public-service apps (see `configs/app_domains.yaml`): 1,000 of the 2,000 annotated items come from the `gov` domain. **Games are excluded** from the annotation sample.
- AURA's sentiment and AURA-Cls labels are **not** our task labels. Sentiment is never shown to coders and never used as a feature. AURA-Cls `bug_report` labels serve only as an **external human proxy** for the complaint gate.
- Neither dataset has review dates, so no temporal analysis is possible from these data. Codex's dashboard must not invent dates for these records.

## Processing and record flow
| stage | count |
|---|---|
| raw records (both sources) | 32,600 |
| excluded: not predominantly Arabic (< 50% Arabic letters) | 6 |
| excluded: too short (< 2 words) | 4 |
| duplicate groups (exact + near-dup, char 3–5-gram cosine ≥ 0.85, union-find, across both sources) | 29,062 |
| records in multi-member groups | 4,998 (largest group 465: formulaic praise) |
| AURA-Cls texts that also appear verbatim in AURA-Sent | 29.9% (grouped together) |
| eligible non-game records | 23,584 → 21,077 unique groups |
| **annotation sample** (1 representative per group) | **2,000**: gov 1,000 / non-gov 700 / AURA-Cls external 300 |
| sample sentiment (AURA-Sent items) | negative 1,275 / positive 427 (negative-weighted, not negative-only) |

Sampling: round-robin across apps with per-app caps (90 gov / 60 non-gov) and seed 42, to avoid one app (e.g. Absher) dominating.

## Privacy
Texts are public app reviews without usernames. Before annotation and modelling, P0 masks URLs, e-mails, @mentions, Saudi mobile numbers (incl. Arabic-Indic digits), and any digit run of 7 or more (IDs, request numbers) with placeholders. Raw files stay local (`data/raw/`, gitignored) and are not redistributed. MIT permits redistribution with attribution, but we publish only ids and labels.

## Limitations
- Public app reviews are self-selected and short (median 41 characters). They are not e-mails, tickets, or screenshots; generalisation to those channels is untested.
- The domain mix is broader than Saudi e-government, and the government subset is ~1,000 annotated items.
- No dates, so no trend claims.
- Labels are AI-assisted reference labels (see `agreement.md`), not independent human gold.
