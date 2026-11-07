"""Report rendering checks; no inference, training or holdout label access."""

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("a4_report", ROOT / "scripts/a4_report.py")
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)

HEADERS = {
    "a4_report.md": (
        "# A4 report", "## Purpose and protocol", "## Data and annotation",
        "## Validation comparison", "## Selection decision log", "## Holdout results", "## Caveats",
    ),
    "a4_model_card.md": (
        "# A4 model card", "## Selected export", "## Decision thresholds and score semantics",
        "## Selection evidence", "## Evaluation", "## Limitations and review",
    ),
    "a4_annotation_provenance.md": (
        "# A4 annotation provenance", "## Counts per set and adjudication",
        "## Coder and adjudicator models", "## Guide versions",
        "## modified_in_a4 and change table", "## Synthetic verification",
    ),
}


def assert_documents(out):
    for name, headers in HEADERS.items():
        path = out / name
        assert path.is_file()
        content = path.read_text(encoding="utf-8")
        for header in headers:
            assert header in content, (name, header)


def write_json(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_current_files_render_with_provenance_projection(tmp_path, monkeypatch):
    import pandas as pd
    import pyarrow.parquet as pq

    original = pq.ParquetFile
    original_csv = pd.read_csv
    projections = []

    def membership_only(path, **kwargs):
        assert Path(path) == ROOT / "data/a4/split_a4.csv"
        assert set(kwargs.get("usecols", [])) == {"set", "a4_split"}
        return original_csv(path, **kwargs)

    class ProvenanceOnly:
        def __init__(self, path):
            assert Path(path) == ROOT / "data/a4/labels_a4.parquet"
            self.parquet = original(path)
            self.schema_arrow = self.parquet.schema_arrow

        def read(self, *, columns):
            assert set(columns) <= set(report.PROVENANCE_COLUMNS)
            assert not {"label_final", "label_a", "label_b", "label_v1", "category", "review"} & set(columns)
            projections.append(columns)
            return self.parquet.read(columns=columns)

    monkeypatch.setattr(pq, "ParquetFile", ProvenanceOnly)
    monkeypatch.setattr(pd, "read_csv", membership_only)
    out = tmp_path / "reports"
    assert report.main(root=ROOT, out_dir=out) == 0
    assert_documents(out)
    if (ROOT / "data/a4/labels_a4.parquet").exists():
        assert projections
    content = (out / "a4_report.md").read_text()
    for path in (ROOT / "results/a4/runs").glob("*/metrics_val.json"):
        assert path.parent.name in content
        metrics = report.read_json(ROOT, path.relative_to(ROOT))
        for key in report.METRICS:
            if metrics.get(key) is not None:
                assert report.cell(metrics[key]) in content
    assert "E0_baseline_v1 validation is contaminated" in content
    assert "configs/a4_selection_rule.yaml" in content
    assert "NON-BLIND" in content


@pytest.mark.parametrize("missing", ["selection.json", "holdout_metrics.json", "both"])
def test_missing_optional_files(tmp_path, missing, capsys):
    root = tmp_path / "inputs"
    # Copy JSON summaries only. Never copy or inspect per-item holdout data.
    for relative in (
        "results/a4/agreement_a4.json", "results/a4/sampling_flow.json",
        "results/a4/label_issues_summary.json", "data/a4/split_a4_info.json",
    ):
        if (ROOT / relative).exists():
            write_json(root, relative, json.loads((ROOT / relative).read_text()))
    if missing == "selection.json":
        write_json(root, "results/a4/holdout_metrics.json", {"selected": "fixture_candidate"})
    if missing == "holdout_metrics.json":
        write_json(root, "results/a4/selection.json", {"selected": "fixture_candidate"})
    out = tmp_path / "reports"
    assert report.main(root=root, out_dir=out) == 0
    assert_documents(out)
    content = (out / "a4_report.md").read_text()
    stdout = capsys.readouterr().out
    for name in ("selection.json", "holdout_metrics.json"):
        if missing in (name, "both"):
            assert f"pending: results/a4/{name}" in content
            assert f"pending: results/a4/{name}" in stdout


def test_empty_or_partial_inputs(tmp_path):
    root = tmp_path / "inputs"
    write_json(root, "results/a4/selection.json", {"candidates": None, "decision_log": None})
    write_json(root, "results/a4/holdout_metrics.json", {"candidates": {"partial": None}, "ci95_holdout_all": None})
    path = root / "results/a4/runs/in_progress/metrics_val.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"e2e_macro_f1":')
    out = tmp_path / "reports"
    assert report.main(root=root, out_dir=out) == 0
    assert_documents(out)
    assert "in_progress" in (out / "a4_report.md").read_text()
    assert "pending" in (out / "a4_annotation_provenance.md").read_text()


def test_published_evaluation_and_selected_manifest(tmp_path):
    root = tmp_path / "inputs"
    chosen = "fixture_selected"
    # Fabricated summary values test formatting, not model performance.
    metrics = {"n": 17, "e2e_macro_f1": 0.7132, "gate_macro_f1": 0.8234, "category_macro_f1": 0.6345,
               "per_class_category": {"PERF": {"precision": 0.6, "recall": 0.5, "f1": 0.5455, "support": 3}},
               "review": {"review_rate": 0.2, "auto_coverage": 0.8, "auto_accuracy": 0.9}}
    candidate = {subset: metrics for subset in report.SUBSETS}
    candidate["v1_test_NOT_BLIND"] = metrics
    selection = {"selected": chosen, "model_version": "fixture-v1", "export_dir": "artifacts/a4/export/fixture-v1",
                 "holdout_used": False, "decision_log": ["fixture decision copied verbatim"]}
    holdout = {"selected": chosen, "model_version": "fixture-v1",
               "candidates": {chosen: candidate, report.BASELINE: candidate},
               "ci95_holdout_all": {"e2e_macro_f1": {"selected": [0.6, 0.8], "baseline": [0.5, 0.7],
                                                      "delta_selected_minus_baseline": [-0.01, 0.12]}},
               "external_aura_proxy": {chosen: {"agreement": 0.84}},
               "cost_selected_export": {"latency_ms": 8.125, "artifact_size_mb": 2.5}}
    write_json(root, "results/a4/selection.json", selection)
    write_json(root, "results/a4/holdout_metrics.json", holdout)
    write_json(root, "artifacts/a4/export/fixture-v1/manifest.json", {
        "selected_candidate": chosen, "model_version": "fixture-v1", "backend": "fixture-backend",
        "thresholds": {"gate_decision": 0.5}, "score_semantics": {"needs_review": "fixture review semantics"},
    })
    write_json(root, "artifacts/a4/export/unselected/manifest.json", {
        "selected_candidate": "wrong", "model_version": "wrong", "backend": "wrong-backend",
    })
    write_json(root, "results/a4/runs/fixture_run/metrics_val.json", {
        **metrics, "temperature": 1.25, "train_minutes": 3.75, "best_epoch": 2,
    })
    out = tmp_path / "reports"
    assert report.main(root=root, out_dir=out) == 0
    assert_documents(out)
    content = (out / "a4_report.md").read_text()
    for text in (*report.SUBSETS, "fixture decision copied verbatim", "0.7132", "0.5455", "8.1250",
                 "delta", "[-0.01, 0.12]", "1.2500", "3.7500", "v1_test_NOT_BLIND", "NON-BLIND"):
        assert text in content
    assert "#### fixture_selected" in content
    assert "#### E0_baseline_v1" in content
    card = (out / "a4_model_card.md").read_text()
    assert "fixture-backend" in card
    assert "fixture review semantics" in card
    assert "wrong-backend" not in card


def test_ambiguous_export_is_pending(tmp_path):
    for version in ("first", "second"):
        write_json(tmp_path, f"artifacts/a4/export/{version}/manifest.json", {"model_version": version})
    assert report.export_manifest(tmp_path, {}, {}) == (None, {})


def test_partial_provenance_and_saved_changes(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = tmp_path / "data/a4/labels_a4.parquet"
    path.parent.mkdir(parents=True)
    # Metadata-only fixture: there are no label-value columns to read.
    pq.write_table(pa.Table.from_pylist([
        {"set": "v1_train", "adjudicated": True, "modified_in_a4": True},
        {"set": "v1_train", "adjudicated": False, "modified_in_a4": False},
        {"set": "synthetic", "adjudicated": False, "modified_in_a4": False},
    ]), path)
    content = report.annotation_provenance(tmp_path, {
        "v1_rereview": {"changes": {"UX->OTHER": 1}, "label_changed": 1},
        "synthetic": {"n_generated": 1, "n_verified": 1},
    })
    assert "| v1_train | 2 | 1 | 0.5000 | 1 |" in content
    assert "| modified_in_a4 | 1 |" in content
    assert "| UX->OTHER | 1 |" in content
    assert "pending: provenance columns" in content
