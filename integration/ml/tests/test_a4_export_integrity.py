"""Integrity and offline contract checks for the exported A4 candidate.

Only exported artifacts and synthetic probe texts are used; no label data is read.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest


EXPORT = Path(__file__).resolve().parents[1] / "artifacts/a4/export/a4-marbert-v1"
LABELS = ("NO", "AUTH", "AVAIL", "PERF", "TRANS", "UX", "OTHER")
CONTRACT_KEYS = {
    "is_complaint",
    "complaint_score",
    "category",
    "category_score",
    "needs_review",
    "model_version",
}
TEXTS = (
    "رمز التحقق لا يصل عند تسجيل الدخول",
    "تطبيق رائع وسهل الاستخدام شكرا لكم",
    "الـ OTP ما يوصلني when I try to login",
    "التطبيق بطيء جدا والصفحة تحمل وقت طويل",
    "الدفع fails عند تأكيد العملية",
)

pytestmark = pytest.mark.skipif(
    not (EXPORT / "model/model.safetensors").is_file(),
    reason=f"A4 export weights absent: {EXPORT / 'model/model.safetensors'}",
)


@pytest.fixture(scope="module", autouse=True)
def offline_infer():
    """Isolate the process cache and restore environment even after a failure."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("ML_ARTIFACT_DIR", str(EXPORT))
        monkeypatch.setenv("HF_HUB_OFFLINE", "1")
        monkeypatch.setenv("TOKENIZERS_PARALLELISM", "false")
        import ml.infer as infer

        try:
            infer._reset_cache()
            yield infer
        finally:
            infer._reset_cache()


@pytest.fixture(scope="module")
def predictions(offline_infer):
    return tuple(offline_infer.predict_text(text) for text in TEXTS)


def test_sha256sums_match_every_listed_file():
    lines = (EXPORT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert lines, "SHA256SUMS must contain at least one checksum"
    seen = set()
    for line_number, line in enumerate(lines, start=1):
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", line)
        assert match is not None, f"Malformed SHA256SUMS line {line_number}: {line!r}"
        expected, relative_path = match.groups()
        path = (EXPORT / relative_path).resolve()
        assert path.is_relative_to(EXPORT.resolve()), f"Checksum path escapes export: {relative_path}"
        assert path not in seen, f"Duplicate checksum entry: {relative_path}"
        seen.add(path)
        assert path.is_file(), f"Checksummed file missing: {relative_path}"
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        assert digest.hexdigest() == expected.lower(), f"SHA256 mismatch: {relative_path}"


def test_manifest_and_label_order():
    manifest = json.loads((EXPORT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["model_version"] == "a4-marbert-v1"
    assert manifest["backend"] == "hf-7way"
    model_dir = manifest["files"]["model_dir"]
    assert isinstance(model_dir, str) and model_dir.strip()
    assert (EXPORT / model_dir).is_dir(), f"Manifest model_dir missing: {model_dir}"
    for key in ("gate_decision", "gate_review_low", "gate_review_high", "category_review"):
        value = manifest["thresholds"][key]
        assert type(value) in (int, float), f"Non-numeric threshold {key}: {value!r}"
        assert 0.0 <= value <= 1.01, f"Threshold outside [0, 1.01]: {key}={value!r}"
    config = json.loads((EXPORT / "model/config.json").read_text(encoding="utf-8"))
    assert config["id2label"] == {str(i): label for i, label in enumerate(LABELS)}


@pytest.mark.parametrize("index", range(len(TEXTS)), ids=("arabic-auth", "arabic-praise", "mixed-auth", "arabic-perf", "mixed-payment"))
def test_predict_text_contract(index, predictions):
    result = predictions[index]
    assert type(result) is dict
    assert set(result) == CONTRACT_KEYS
    assert type(result["is_complaint"]) is bool
    assert type(result["needs_review"]) is bool
    assert type(result["model_version"]) is str
    assert result["model_version"] == "a4-marbert-v1"
    assert type(result["complaint_score"]) is float
    assert 0.0 <= result["complaint_score"] <= 1.0
    if result["is_complaint"]:
        assert type(result["category"]) is str
        assert result["category"] in LABELS[1:]
        assert type(result["category_score"]) is float
        assert 0.0 <= result["category_score"] <= 1.0
    else:
        assert result["category"] is None
        assert result["category_score"] is None


@pytest.mark.parametrize("text", (" ", "\t\n  ", "\u2003\u00a0"), ids=("space", "tabs-newlines", "unicode-spaces"))
def test_whitespace_raises_value_error(text, offline_infer):
    with pytest.raises(ValueError, match="empty or whitespace"):
        offline_infer.predict_text(text)


def test_predictions_match_direct_hf_probabilities(predictions):
    import numpy as np

    from ml.src.hf_model import HFPredictor

    probabilities = HFPredictor(EXPORT / "model").predict_proba(TEXTS)
    assert probabilities.shape == (len(TEXTS), len(LABELS))
    assert np.isfinite(probabilities).all()
    assert ((0.0 <= probabilities) & (probabilities <= 1.0)).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, rtol=0, atol=1e-6)
    for text, result, row in zip(TEXTS, predictions, probabilities, strict=True):
        assert result["complaint_score"] == round(float(1.0 - row[0]), 4), text
        if result["is_complaint"]:
            assert result["category"] == LABELS[1 + int(row[1:].argmax())], text


def test_model_loaded_once_across_repeated_calls(offline_infer, predictions):
    first_model = offline_infer._model
    assert first_model is not None
    for text, expected in zip(TEXTS, predictions, strict=True):
        assert offline_infer.predict_text(text) == expected
        assert offline_infer._model is first_model
