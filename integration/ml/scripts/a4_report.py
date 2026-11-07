"""Render A4 reports from saved evidence, without loading models or label values.

Usage from ml/: PYTHONPATH=.. .venv/bin/python scripts/a4_report.py
Only reports/*.md are written. Missing or incomplete evidence is reported as pending.
The parquet projection contains provenance metadata only; holdout metrics are copied
from the published JSON, never calculated here. Selection is never recomputed.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "E0_baseline_v1"
METRICS = ("e2e_macro_f1", "gate_macro_f1", "category_macro_f1")
SUBSETS = ("holdout_all", "holdout_random", "holdout_enriched", "holdout_codeswitch")
PROVENANCE_COLUMNS = (
    "set", "stratum", "coder_a_model", "coder_b_model", "adjudicator_model",
    "guide_version", "adjudicated", "modified_in_a4", "synthetic_verified",
)


def mapping(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def read_json(root: Path, relative: str | Path) -> dict:
    """Incomplete JSON can occur while an experiment is still writing its result."""
    try:
        value = json.loads((root / relative).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("expected a JSON object")
        return value
    except (OSError, ValueError) as exc:
        print(f"pending: {relative} ({exc})")
        return {}


def cell(value: Any) -> str:
    if value is None:
        return "pending"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.4f}" if math.isfinite(value) else "pending"
    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
        "|", "\\|"
    ).replace("\n", "<br>").replace("\r", "")


def table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
    rows = list(rows)
    if not rows:
        return "pending: no entries available."
    headers = list(headers)
    lines = ["| " + " | ".join(cell(h) for h in headers) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)


def flatten(data: dict, prefix: str = "") -> list[tuple[str, Any]]:
    rows = []
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict) and value:
            rows.extend(flatten(value, name))
        else:
            rows.append((name, value))
    return rows


def details(title: str, data: Any) -> str:
    return f"### {title}\n\n" + table(("Field", "Recorded value"), flatten(mapping(data)))


def sourced(title: str, source: str, data: dict) -> str:
    return f"### {title}\n\nSource: `{source}`.\n\n" + (
        table(("Field", "Recorded value"), flatten(data)) if data else f"pending: {source}."
    )


def contamination_note(root: Path) -> str:
    """Read only CSV split membership, never its label_final column."""
    source = "data/a4/split_a4.csv"
    warning = f"**{BASELINE} validation is contaminated**"
    try:
        import pandas as pd

        splits = pd.read_csv(root / source, usecols=["set", "a4_split"])
        val = splits[splits["a4_split"] == "val"]
        if val.empty:
            raise ValueError("validation membership is unavailable")
        overlap = int((val["set"] == "v1_train").sum())
        return (f"{warning}: {overlap}/{len(val)} val items were in v1 training "
                f"(source: `{source}`, membership columns only). Treat it as a reference; "
                "its validation score is unsuitable for an independent comparison.")
    except (ImportError, OSError, ValueError) as exc:
        print(f"pending: {source} ({exc})")
        return f"{warning}; pending: overlap counts from `{source}`."


def validation(root: Path) -> str:
    columns = (*METRICS, "recall_TRANS", "recall_UX", "temperature", "train_minutes", "best_epoch")
    rows = []
    for path in sorted((root / "results/a4/runs").glob("*/metrics_val.json")):
        metrics = read_json(root, path.relative_to(root))
        rows.append((path.parent.name, metrics.get("n"), *(metrics.get(k) for k in columns)))
    return "\n\n".join((
        "## Validation comparison",
        "Source: `results/a4/runs/*/metrics_val.json`. All available runs are listed; "
        "missing fields are pending. `n` is the evaluated count recorded by each run; "
        "split counts include UNCLEAR, which the protocol excludes from scoring.",
        table(("Run", "n", *columns), rows),
        contamination_note(root),
    ))


def selection_section(selection: dict) -> str:
    parts = ["## Selection decision log", "Source: `results/a4/selection.json`."]
    if not selection:
        return "\n\n".join((*parts, "pending: results/a4/selection.json."))
    summary = {k: selection.get(k) for k in (
        "selected", "model_version", "export_dir", "rule", "decided_utc", "code_commit", "holdout_used"
    )}
    parts.append(table(("Field", "Recorded value"), flatten(summary)))
    log = selection.get("decision_log")
    if isinstance(log, list) and log:
        parts.append("\n".join(f"- {cell(entry)}" for entry in log))
    elif log:
        parts.append(cell(log))
    else:
        parts.append("pending: selection decision_log.")
    parts.extend(details(title, selection.get(key)) for title, key in (
        ("Selection validation table", "validation_table"),
        ("Seed families and median export run", "families"),
        ("Candidate export runs, validation thresholds and review", "candidates"),
    ))
    return "\n\n".join(parts)


def selected_name(selection: dict, holdout: dict) -> str | None:
    name = selection.get("selected") or holdout.get("selected")
    return name if isinstance(name, str) else None


def holdout_section(selection: dict, holdout: dict) -> str:
    parts = [
        "## Holdout results",
        "Source: `results/a4/holdout_metrics.json`. These are saved evaluation summaries; "
        "this renderer does not access holdout labels or recompute scores.",
    ]
    if not holdout:
        parts.append("pending: results/a4/holdout_metrics.json.")
    else:
        parts.append(table(("Field", "Recorded value"), [
            (key, holdout.get(key)) for key in (
                "selected", "model_version", "holdout_n_excl_unclear", "label_note"
            )
        ]))
    candidates = mapping(holdout.get("candidates"))
    rows, reviews, nonblind = [], [], []
    for name, candidate in sorted(candidates.items()):
        candidate = mapping(candidate)
        for subset in SUBSETS:
            metrics = mapping(candidate.get(subset))
            rows.append((name, subset, metrics.get("n"), *(metrics.get(k) for k in METRICS)))
            review = mapping(metrics.get("review"))
            reviews.append((name, subset, review.get("review_rate"), review.get("auto_coverage"),
                            review.get("auto_accuracy"), review.get("auto_complaint_coverage")))
        v1 = mapping(candidate.get("v1_test_NOT_BLIND"))
        nonblind.append((name, v1.get("n"), *(v1.get(k) for k in METRICS)))
    parts.extend((
        "### Candidate metrics by holdout subset",
        table(("Candidate", "Subset", "n", *METRICS), rows),
        "### Review and automatic decisions",
        table(("Candidate", "Subset", "review_rate", "auto_coverage", "auto_accuracy",
               "auto_complaint_coverage"), reviews),
        "### Per-class category precision / recall / F1",
        "The following tables use `holdout_all.per_class_category` only.",
    ))
    chosen = selected_name(selection, holdout)
    for name in dict.fromkeys((chosen, BASELINE)):
        if name is None:
            parts.append("pending: selected candidate identity.")
            continue
        per_class = mapping(mapping(mapping(candidates.get(name)).get("holdout_all")).get("per_class_category"))
        parts.append(f"#### {cell(name)}\n\n" + table(
            ("Category", "Precision", "Recall", "F1", "Support"),
            ((category, *(mapping(values).get(k) for k in ("precision", "recall", "f1", "support")))
             for category, values in per_class.items()),
        ))
    ci = mapping(holdout.get("ci95_holdout_all"))
    parts.extend((
        "### ci95_holdout_all — paired delta",
        "Intervals are copied from the saved bootstrap results. The paired delta is "
        "selected minus baseline; no bootstrap is run here.",
        table(("Metric", "Selected CI", "Baseline CI", "Paired delta: selected minus baseline CI"),
              ((key, mapping(values).get("selected"), mapping(values).get("baseline"),
                mapping(values).get("delta_selected_minus_baseline")) for key, values in ci.items())),
        details("external_aura_proxy", holdout.get("external_aura_proxy")),
        "AURA bug-report agreement is an external gate proxy, not a category benchmark.",
        details("cost_selected_export", holdout.get("cost_selected_export")),
        "Latency note: " + cell(holdout.get("latency_note")),
        "### v1_test_NOT_BLIND — NON-BLIND secondary comparison",
        "v1 test is a non-blind secondary comparison and is not evidence for selecting a candidate.",
        table(("Candidate", "n", *METRICS), nonblind),
    ))
    return "\n\n".join(parts)


def caveats(agreement: dict) -> str:
    synthetic = mapping(agreement.get("synthetic"))
    verified, generated = synthetic.get("n_verified"), synthetic.get("n_generated")
    verification = (
        f"Synthetic verification: {cell(verified)}/{cell(generated)} by a blind verifier; "
        "synthetic examples are prototypical."
        if verified is not None and generated is not None
        else "pending: synthetic verification counts; verification uses a blind verifier, "
             "but synthetic examples are prototypical."
    )
    return "\n\n".join(("## Caveats", "\n".join((
        "- AI-assisted reference labels are not human gold.",
        "- Holdout differs from v1 test, so v1 numbers 0.845/0.568/0.553 are not directly comparable.",
        "- PERF has small n.",
        "- Code-switching is rare.",
        f"- {verification}",
    ))))


def report(root: Path, sources: dict[str, dict]) -> str:
    rule = "configs/a4_selection_rule.yaml"
    try:
        protocol = "```yaml\n" + (root / rule).read_text(encoding="utf-8").rstrip() + "\n```"
    except (OSError, UnicodeError) as exc:
        print(f"pending: {rule} ({exc})")
        protocol = f"pending: {rule}."
    agreement = sources["agreement_a4"]
    return "\n\n".join((
        "# A4 report",
        "## Purpose and protocol",
        "Document A4 data, annotation, validation comparisons, the recorded selection and "
        "subsequent evaluation using existing evidence only. Selection and review thresholds "
        "use validation; holdout evaluation follows frozen selection.",
        f"Protocol: [{rule}](../{rule}). The saved protocol is reproduced below.",
        protocol,
        "## Data and annotation",
        sourced("Annotation agreement", "results/a4/agreement_a4.json", agreement),
        sourced("Sampling flow", "results/a4/sampling_flow.json", sources["sampling_flow"]),
        sourced("Split information", "data/a4/split_a4_info.json", sources["split_a4_info"]),
        sourced("Label issues", "results/a4/label_issues_summary.json", sources["label_issues_summary"]),
        validation(root),
        selection_section(sources["selection"]),
        holdout_section(sources["selection"], sources["holdout_metrics"]),
        caveats(agreement),
    )) + "\n"


def export_manifest(root: Path, selection: dict, holdout: dict) -> tuple[str | None, dict]:
    """Resolve the recorded selected export; never pick an arbitrary latest export."""
    manifests = [(p, read_json(root, p.relative_to(root)))
                 for p in sorted((root / "artifacts/a4/export").glob("*/manifest.json"))]
    chosen = selected_name(selection, holdout)
    version = selection.get("model_version") or holdout.get("model_version")
    export = selection.get("export_dir")
    matches = []
    for path, manifest in manifests:
        if not manifest:
            continue
        if export and str(path.parent.relative_to(root)) != str(export).rstrip("/"):
            continue
        if version and manifest.get("model_version") != version:
            continue
        if chosen and manifest.get("selected_candidate") != chosen:
            continue
        matches.append((str(path.relative_to(root)), manifest))
    return matches[0] if len(matches) == 1 else (None, {})


def model_card(root: Path, sources: dict[str, dict]) -> str:
    selection, holdout = sources["selection"], sources["holdout_metrics"]
    path, manifest = export_manifest(root, selection, holdout)
    parts = [
        "# A4 model card",
        "## Selected export",
        "Intended use: complaint triage and complaint category assignment with a review path "
        "for uncertain decisions. This card describes the recorded selected export.",
        f"Source: `{path}`." if path else
        "pending: an unambiguous selected export in artifacts/a4/export/*/manifest.json.",
        details("Export identity and provenance", {key: manifest.get(key) for key in (
            "model_version", "backend", "selected_candidate", "artifact_run", "created_utc",
            "code_commit", "label_provenance", "categories", "files",
        )}),
        "## Decision thresholds and score semantics",
        details("Thresholds", manifest.get("thresholds")),
        details("Score semantics", manifest.get("score_semantics")),
        "## Selection evidence",
        selection_section(selection).replace("## Selection decision log", "### Selection decision log", 1),
        "## Evaluation",
    ]
    chosen = selected_name(selection, holdout) or manifest.get("selected_candidate")
    candidate = mapping(mapping(holdout.get("candidates")).get(chosen))
    parts.append(table(("Subset", "n", *METRICS), (
        (subset, mapping(candidate.get(subset)).get("n"),
         *(mapping(candidate.get(subset)).get(k) for k in METRICS)) for subset in SUBSETS
    )))
    if not candidate:
        parts.append("pending: selected export holdout evaluation in results/a4/holdout_metrics.json.")
    parts.extend((
        details("holdout_all review and automatic decisions", mapping(candidate.get("holdout_all")).get("review")),
        details("ci95_holdout_all including paired delta", holdout.get("ci95_holdout_all")),
        details("external_aura_proxy", mapping(holdout.get("external_aura_proxy")).get(chosen)),
        details("cost_selected_export", holdout.get("cost_selected_export")),
        "### v1_test_NOT_BLIND — NON-BLIND secondary comparison",
        table(("Metric", "Recorded value"), flatten(mapping(candidate.get("v1_test_NOT_BLIND")))),
        "## Limitations and review",
        "Review flags and thresholds must be interpreted with the recorded score semantics. "
        "The evidence does not establish human-gold accuracy or performance outside the sampled data.",
        caveats(sources["agreement_a4"]),
    ))
    return "\n\n".join(parts) + "\n"


def provenance_rows(root: Path) -> tuple[list[dict], set[str]]:
    source = "data/a4/labels_a4.parquet"
    try:
        import pyarrow.parquet as pq

        parquet = pq.ParquetFile(root / source)
        available = set(parquet.schema_arrow.names)
        columns = [c for c in PROVENANCE_COLUMNS if c in available]
        if "set" not in columns:
            raise ValueError("missing set provenance column")
        # Explicit allowlist: no text, category, complaint, or label columns are read.
        return parquet.read(columns=columns).to_pylist(), set(columns)
    except (ImportError, OSError, ValueError) as exc:
        print(f"pending: {source} ({exc})")
        return [], set()


def flag_summary(rows: list[dict], key: str) -> tuple[Any, Any]:
    known = [row[key] for row in rows if isinstance(row.get(key), bool)]
    return (sum(known), sum(known) / len(known)) if known else (None, None)


def annotation_provenance(root: Path, agreement: dict) -> str:
    rows, columns = provenance_rows(root)
    parts = [
        "# A4 annotation provenance",
        "Source: `data/a4/labels_a4.parquet`, provenance columns only. Label-value and text "
        "columns are never read, including on holdout. Existing agreement JSON supplies the "
        "aggregate v1 re-review change table and synthetic verification summary.",
        "## Counts per set and adjudication",
    ]
    if not rows:
        parts.append("pending: data/a4/labels_a4.parquet provenance rows.")
    missing = sorted(set(PROVENANCE_COLUMNS) - columns)
    if missing:
        parts.append("pending: provenance columns " + ", ".join(missing) + ".")
    groups = {}
    for row in rows:
        groups.setdefault(row.get("set") or "unknown", []).append(row)
    parts.append(table(("Set", "Count", "Adjudicated count", "Adjudicated rate", "modified_in_a4 count"), (
        (name, len(group), *flag_summary(group, "adjudicated"), flag_summary(group, "modified_in_a4")[0])
        for name, group in sorted(groups.items())
    )))
    parts.append("Adjudicated rates use non-null boolean flags as the denominator; missing flags "
                 "are pending. Counts describe the stored provenance, including inherited v1 annotations.")
    parts.append("## Coder and adjudicator models")
    model_rows, guide_rows = [], []
    for name, group in sorted(groups.items()):
        for role in ("coder_a_model", "coder_b_model", "adjudicator_model"):
            for model, count in sorted(Counter(cell(row.get(role)) for row in group).items()):
                model_rows.append((name, role, model, count))
        for version, count in sorted(Counter(cell(row.get("guide_version")) for row in group).items()):
            guide_rows.append((name, version, count))
    parts.extend((
        table(("Set", "Role", "Stored model", "Count"), model_rows),
        "A pending adjudicator model may be null for synthetic items with a blind verifier; "
        "a stored adjudicator model does not imply that every item was adjudicated.",
        "## Guide versions",
        table(("Set", "guide_version", "Count"), guide_rows),
        "## modified_in_a4 and change table",
        table(("Field", "Count"), [("modified_in_a4", flag_summary(rows, "modified_in_a4")[0])]),
        "Source for label transitions: `results/a4/agreement_a4.json`, `v1_rereview.changes` "
        "(precomputed v1 train/validation re-review only). No per-item labels are accessed.",
        table(("Change (v1 to A4)", "Count"), mapping(mapping(agreement.get("v1_rereview")).get("changes")).items()),
        details("v1 re-review summary", {key: value for key, value in mapping(agreement.get("v1_rereview")).items()
                                           if key != "changes"}),
        "## Synthetic verification",
        sourced("Saved verification summary", "results/a4/agreement_a4.json:synthetic", mapping(agreement.get("synthetic"))),
    ))
    synthetic = groups.get("synthetic", [])
    by_kind = {}
    for row in synthetic:
        by_kind.setdefault(row.get("stratum") or "unknown", []).append(row)
    parts.append(table(("Synthetic stratum", "Count", "Verified count", "Verified rate"), (
        (name, len(group), *flag_summary(group, "synthetic_verified")) for name, group in sorted(by_kind.items())
    )))
    parts.append("Synthetic generator intent and blind verifier identities are recorded in the "
                 "model table above. Verification agreement does not make these prototypical examples human gold.")
    parts.append(caveats(agreement))
    return "\n\n".join(parts) + "\n"


def main(root: str | Path = ROOT, out_dir: str | Path | None = None) -> int:
    root = Path(root)
    destination = Path(out_dir) if out_dir is not None else root / "reports"
    sources = {name: read_json(root, path) for name, path in (
        ("agreement_a4", "results/a4/agreement_a4.json"),
        ("sampling_flow", "results/a4/sampling_flow.json"),
        ("split_a4_info", "data/a4/split_a4_info.json"),
        ("label_issues_summary", "results/a4/label_issues_summary.json"),
        ("selection", "results/a4/selection.json"),
        ("holdout_metrics", "results/a4/holdout_metrics.json"),
    )}
    documents = {
        "a4_report.md": report(root, sources),
        "a4_model_card.md": model_card(root, sources),
        "a4_annotation_provenance.md": annotation_provenance(root, sources["agreement_a4"]),
    }
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in documents.items():
        path = destination / name
        path.write_text(content, encoding="utf-8")
        print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
