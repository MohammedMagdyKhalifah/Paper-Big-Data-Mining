"""Offline P1 integration with the real MARBERT export and recorded scenarios."""

import json
import sys
from pathlib import Path

import pytest

import ml.infer as infer
from ml.analyze import analyze, error_cues, narrative_markers, warmup
from ml.src.ocr import OCRUnavailableError, extract_text, get_engine


ML = Path(__file__).resolve().parents[1]
EXPORT = ML / "artifacts/a4/export/a4-marbert-v1"
FIXTURES = ML / "tests/fixtures/p1"
SAMPLES = json.loads((FIXTURES / "sample_outputs.json").read_text(encoding="utf-8"))
ANALYSIS_KEYS = {
    "schema_version", "analysis_kind", "input", "prediction", "systems",
    "signals", "ocr", "notes", "timing_ms",
}
PREDICTION_KEYS = {
    "is_complaint", "complaint_score", "category", "category_score", "needs_review", "model_version",
}

pytestmark = pytest.mark.skipif(
    not (EXPORT / "model/model.safetensors").is_file(),
    reason="real a4-marbert-v1 export weights are absent",
)


@pytest.fixture(scope="module", autouse=True)
def real_marbert():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("ML_ARTIFACT_DIR", str(EXPORT))
        monkeypatch.setenv("HF_HUB_OFFLINE", "1")
        monkeypatch.setenv("TOKENIZERS_PARALLELISM", "false")
        monkeypatch.delenv("ML_SYSTEMS_REGISTRY", raising=False)
        from ml.src import systems

        monkeypatch.setattr(systems, "_registry", None)
        infer._reset_cache()
        try:
            yield
        finally:
            infer._reset_cache()


@pytest.fixture(scope="module")
def vision_engine():
    if sys.platform != "darwin":
        pytest.skip("recorded screenshot scenarios require Apple Vision on macOS")
    try:
        get_engine("vision")
    except OCRUnavailableError as exc:
        pytest.skip(str(exc))
    return "vision"


def _check_contract(result):
    assert set(result) == ANALYSIS_KEYS
    assert result["schema_version"] == "p1-analysis-v1"
    prediction = result["prediction"]
    if prediction is not None:
        assert set(prediction) == PREDICTION_KEYS
        assert prediction == infer.predict_text(result["input"]["classified_text"])
        assert prediction["model_version"] == "a4-marbert-v1"
    assert result["timing_ms"]["total_ms"] >= 0


def _check_cue_spans(result):
    text = result["input"]["classified_text"]
    cues = result["signals"]["error_message_cues"]
    assert cues
    for cue in cues:
        assert 0 <= cue["start"] < cue["end"] <= len(text)
        assert text[cue["start"]:cue["end"]] == cue["text"]


def test_text_only_complaint_preserves_prediction_contract():
    text = SAMPLES["arabic_text_auth"]["input"]["text"]
    result = analyze(text=text)
    _check_contract(result)
    assert result["analysis_kind"] == "complaint"
    assert result["ocr"] is None
    assert result["input"]["text_source"] == "user_text"
    assert result["input"]["classified_text"] == text
    assert result["input"]["has_image"] is False


def test_praise_is_not_a_complaint():
    result = analyze(text=SAMPLES["arabic_text_praise"]["input"]["text"])
    _check_contract(result)
    assert result["analysis_kind"] == "not_complaint"
    assert result["prediction"]["is_complaint"] is False
    assert result["prediction"]["category"] is None
    assert result["prediction"]["category_score"] is None


def test_image_only_error_screen_needs_context(vision_engine):
    result = analyze(image=FIXTURES / "err00.png", ocr_engine=vision_engine)
    _check_contract(result)
    assert result["analysis_kind"] == "error_screen_signal"
    assert result["signals"]["needs_user_context"] is True
    assert result["prediction"] is not None
    assert result["input"]["text_source"] == "ocr"
    _check_cue_spans(result)


def test_error_screen_with_user_text_is_classified_as_narrative(vision_engine):
    text = "من أمس ما أقدر أجدد الهوية"
    result = analyze(text=text, image=FIXTURES / "err00.png", ocr_engine=vision_engine)
    _check_contract(result)
    assert result["analysis_kind"] != "error_screen_signal"
    assert result["signals"]["needs_user_context"] is False
    assert result["input"]["text_source"] == "user_text+ocr"
    assert result["input"]["classified_text"] == text + "\n" + result["ocr"]["text"]
    _check_cue_spans(result)
    local_cues = error_cues(result["ocr"]["text"])
    offset = len(text) + 1
    assert result["signals"]["error_message_cues"] == [
        {**cue, "start": cue["start"] + offset, "end": cue["end"] + offset} for cue in local_cues
    ]


def test_chat_narrative_is_not_an_error_screen(vision_engine):
    result = analyze(image=FIXTURES / "chat03.png", ocr_engine=vision_engine)
    _check_contract(result)
    assert result["ocr"]["status"] == "ok"
    assert result["analysis_kind"] != "error_screen_signal"
    assert result["signals"]["narrative_markers"]
    assert result["signals"]["needs_user_context"] is False


def test_blank_image_has_nothing_to_classify(vision_engine):
    result = analyze(image=FIXTURES / "notext0.png", ocr_engine=vision_engine)
    _check_contract(result)
    assert result["analysis_kind"] == "no_text"
    assert result["prediction"] is None
    assert result["systems"] is None
    assert result["input"]["classified_text"] is None
    assert result["ocr"]["status"] == "empty"


def test_corrupt_image_is_ocr_failed(vision_engine):
    result = analyze(image=FIXTURES / "corrupt.png", ocr_engine=vision_engine)
    _check_contract(result)
    assert result["analysis_kind"] == "ocr_failed"
    assert result["prediction"] is None
    assert result["systems"] is None
    assert result["ocr"]["error"]["code"] == "unreadable_image"


def test_corrupt_image_with_user_text_still_classifies(vision_engine):
    text = "تطبيق أبشر ما يفتح من أمس"
    result = analyze(text=text, image=FIXTURES / "corrupt.png", ocr_engine=vision_engine)
    _check_contract(result)
    assert result["analysis_kind"] == "complaint"
    assert result["input"]["text_source"] == "user_text"
    assert result["input"]["classified_text"] == text
    assert result["prediction"] == infer.predict_text(text)
    assert result["ocr"]["status"] == "failed"
    assert any("ocr" in note.lower() and "fail" in note.lower() for note in result["notes"])


def test_two_step_flow_uses_corrected_ocr_text(vision_engine):
    ocr = extract_text(FIXTURES / "err03.png", engine=vision_engine)
    assert ocr["status"] == "ok", ocr["error"]
    corrected = "منصة نفاذ: رمز التحقق غير صحيح"
    result = analyze(image_ocr=ocr, corrected_text=corrected)
    _check_contract(result)
    assert result["input"]["text_source"] == "ocr_corrected"
    assert result["input"]["classified_text"] == corrected
    assert result["ocr"]["corrected_text"] == corrected
    assert result["ocr"]["text"] == ocr["text"]
    assert result["systems"]["status"] == "identified"
    assert [system["system_id"] for system in result["systems"]["systems"]] == ["nafath"]
    assert "corrected_text" not in ocr
    _check_cue_spans(result)


@pytest.mark.parametrize("kwargs", [{}, {"text": ""}, {"text": " \n\t "}, {"corrected_text": "   "}])
def test_missing_or_whitespace_input_raises(kwargs):
    with pytest.raises(ValueError, match="nothing to analyse"):
        analyze(**kwargs)


def test_image_and_image_ocr_are_mutually_exclusive():
    with pytest.raises(ValueError, match="either image or image_ocr"):
        analyze(image=FIXTURES / "err00.png", image_ocr={"status": "ok"})


@pytest.mark.parametrize("text", [42, b"complaint", [], {}])
def test_non_string_text_raises(text):
    with pytest.raises(TypeError, match="text must be str"):
        analyze(text=text)


def test_non_string_corrected_text_raises():
    with pytest.raises(TypeError, match="corrected_text must be str"):
        analyze(corrected_text=42)


@pytest.mark.parametrize("value", ["ocr text", [], {}])
def test_invalid_previous_ocr_raises(value):
    with pytest.raises(TypeError, match="image_ocr must be a dict"):
        analyze(image_ocr=value)


def test_warmup_loads_real_export(vision_engine):
    result = warmup(ocr_engine=vision_engine)
    assert result["model_version"] == "a4-marbert-v1"
    assert result["ocr_engine"] == get_engine(vision_engine).name
    assert result["elapsed_s"] >= 0


@pytest.mark.parametrize(
    "text, expected",
    [
        ("عذرا، حَدَث خَطَأ. حاول مرة أخرى", ["عذرا", "حَدَث خَطَأ", "حاول مرة أخرى"]),
        ("Network error; try again", ["Network error", "try again"]),
        ("رمز التحقق غير صحيح", ["غير صحيح"]),
        ("terror is not an errorfree match", []),
    ],
)
def test_error_cues_are_non_overlapping_original_spans(text, expected):
    cues = error_cues(text)
    assert [cue["text"] for cue in cues] == expected
    for cue in cues:
        assert text[cue["start"]:cue["end"]] == cue["text"]
    for left, right in zip(cues, cues[1:]):
        assert left["end"] <= right["start"]


@pytest.mark.parametrize(
    "text, has_narrative",
    [("أنا حاولت أدفع ويطلع لي خطأ", True), ("I cannot log in", True), ("حدث خطأ، حاول مرة أخرى", False), ("", False)],
)
def test_narrative_marker_distinguishes_user_description(text, has_narrative):
    assert bool(narrative_markers(text)) is has_narrative


@pytest.mark.parametrize("scenario_name", list(SAMPLES))
def test_recorded_scenario_regression(scenario_name, request):
    scenario = SAMPLES[scenario_name]
    kwargs = dict(scenario["input"])
    if "image" in kwargs:
        kwargs["image"] = FIXTURES / kwargs["image"]
        kwargs["ocr_engine"] = request.getfixturevalue("vision_engine")
    actual = analyze(**kwargs)
    expected = scenario["output"]
    _check_contract(actual)
    assert actual["analysis_kind"] == expected["analysis_kind"], actual["ocr"]["error"] if actual["ocr"] else None
    if expected["prediction"] is None:
        assert actual["prediction"] is None
    else:
        assert actual["prediction"] is not None
        assert actual["prediction"]["is_complaint"] == expected["prediction"]["is_complaint"]
        assert actual["prediction"]["category"] == expected["prediction"]["category"]
    if expected["systems"] is None:
        assert actual["systems"] is None
    else:
        assert actual["systems"] is not None
        assert actual["systems"]["status"] == expected["systems"]["status"]
