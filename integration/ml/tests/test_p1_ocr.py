"""P1 OCR contracts, image validation, and small edit-distance examples."""

import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from ml.src import ocr
from ml.src.ocr_metrics import cer_wer


ML = Path(__file__).resolve().parents[1]
FIXTURES = ML / "tests/fixtures/p1"
RESULT_KEYS = {
    "status", "text", "lines", "mean_confidence", "low_confidence",
    "error", "engine", "image", "elapsed_ms",
}


def _check_result(result):
    assert set(result) == RESULT_KEYS
    assert result["status"] in {"ok", "empty", "failed"}
    assert isinstance(result["text"], str)
    assert isinstance(result["lines"], list)
    assert isinstance(result["low_confidence"], bool)
    assert isinstance(result["engine"], str) and result["engine"]
    assert result["elapsed_ms"] >= 0
    for confidence in [result["mean_confidence"], *(line["confidence"] for line in result["lines"])]:
        assert confidence is None or 0.0 <= confidence <= 1.0
    assert result["text"] == "\n".join(line["text"] for line in result["lines"])
    if result["status"] == "failed":
        assert result["text"] == ""
        assert result["lines"] == []
        assert result["mean_confidence"] is None
        assert result["low_confidence"] is False
        assert result["error"]["code"]
        assert result["error"]["message"]
    else:
        assert result["error"] is None


@pytest.fixture(scope="module")
def vision_engine():
    if sys.platform != "darwin":
        pytest.skip("Apple Vision OCR requires macOS")
    try:
        ocr.get_engine("vision")
    except ocr.OCRUnavailableError as exc:
        pytest.skip(str(exc))
    return "vision"


@pytest.fixture
def validation_engine(monkeypatch):
    """Use real image decoding without requiring an installed recognizer."""
    def unexpected_run(image):
        pytest.fail("an invalid image must be rejected before recognition")

    monkeypatch.setitem(
        ocr._engines, "vision", SimpleNamespace(name="validation-only", run=unexpected_run),
    )
    return "vision"


def test_vision_error_screen_has_text(vision_engine):
    result = ocr.extract_text(FIXTURES / "err00.png", engine=vision_engine)
    _check_result(result)
    assert result["status"] == "ok", result["error"]
    assert result["text"].strip()
    assert result["lines"]


def test_blank_image_is_empty(vision_engine):
    result = ocr.extract_text(FIXTURES / "notext0.png", engine=vision_engine)
    _check_result(result)
    assert result["status"] == "empty", result["error"]
    assert result["text"] == ""
    assert result["lines"] == []
    assert result["mean_confidence"] is None
    assert result["low_confidence"] is False


@pytest.mark.parametrize(
    "image, code",
    [
        pytest.param(FIXTURES / "corrupt.png", "unreadable_image", id="corrupt-png"),
        pytest.param(b"", "unreadable_image", id="empty-bytes"),
        pytest.param(bytes(range(256)), "unreadable_image", id="random-bytes"),
        pytest.param(FIXTURES / "tiny.gif", "unsupported_format", id="gif"),
    ],
)
def test_bad_images_return_failed(image, code, validation_engine):
    result = ocr.extract_text(image, engine=validation_engine)
    _check_result(result)
    assert result["status"] == "failed"
    assert result["error"]["code"] == code


def test_missing_path_returns_file_not_found(tmp_path, validation_engine):
    path = tmp_path / "missing.png"
    result = ocr.extract_text(path, engine=validation_engine)
    _check_result(result)
    assert result["status"] == "failed"
    assert result["error"]["code"] == "file_not_found"


def test_integer_image_raises_type_error(validation_engine):
    with pytest.raises(TypeError, match="image must be"):
        ocr.extract_text(42, engine=validation_engine)


@pytest.mark.parametrize("representation", ["path", "str", "bytes", "pil"])
def test_load_image_accepts_equivalent_inputs(representation):
    path = FIXTURES / "err00.png"
    with Image.open(path) as original:
        source = {"path": path, "str": str(path), "bytes": path.read_bytes(), "pil": original}[representation]
        loaded, info = ocr.load_image(source)
        assert loaded.mode == "RGB"
        assert loaded.size == original.size
        assert loaded.tobytes() == original.convert("RGB").tobytes()
        assert info == {"format": "PNG", "width": original.width, "height": original.height}


def test_extract_text_agrees_for_path_bytes_and_pil(vision_engine):
    path = FIXTURES / "err00.png"
    with Image.open(path) as image:
        results = [ocr.extract_text(source, engine=vision_engine) for source in (path, path.read_bytes(), image)]
    for result in results:
        _check_result(result)
        assert result["status"] == "ok", result["error"]
    assert results[0]["text"] == results[1]["text"] == results[2]["text"]
    assert results[0]["image"] == results[1]["image"] == results[2]["image"]


def test_tesseract_error_screen():
    tessdata = ML / "artifacts/ocr/tessdata"
    if not (tessdata / "ara.traineddata").is_file():
        pytest.skip("local Arabic Tesseract traineddata is absent")
    if not (shutil.which("tesseract") or Path("/opt/homebrew/bin/tesseract").is_file()):
        pytest.skip("Tesseract binary is absent")
    try:
        result = ocr.extract_text(FIXTURES / "err00.png", engine="tesseract")
    except ocr.OCRUnavailableError as exc:
        pytest.skip(str(exc))
    _check_result(result)
    assert result["status"] == "ok", result["error"]
    assert result["text"].strip()
    assert result["engine"].startswith("tesseract-")


@pytest.mark.parametrize("name", ["vision", "easyocr", "tesseract", "paddle"])
def test_get_engine_honours_environment_and_reuses_instance(name, monkeypatch):
    calls = []
    instance = SimpleNamespace(name=f"test-{name}")

    def factory():
        calls.append(name)
        return instance

    monkeypatch.setattr(ocr, "_engines", {})
    monkeypatch.setitem(ocr._ENGINES, name, factory)
    monkeypatch.setenv("ML_OCR_ENGINE", name)
    assert ocr.get_engine() is instance
    assert ocr.get_engine(name) is instance
    assert calls == [name]


def test_unknown_engine_raises_value_error():
    with pytest.raises(ValueError, match="unknown OCR engine"):
        ocr.get_engine("p1-unknown-engine")
    with pytest.raises(ValueError, match="unknown OCR engine"):
        ocr.extract_text(FIXTURES / "err00.png", engine="p1-unknown-engine")


@pytest.mark.parametrize("confidence, low", [(0.0, True), (0.59, True), (0.60, False), (1.0, False), (None, False)])
def test_confidence_review_threshold(confidence, low, monkeypatch):
    line = {"text": "نص", "confidence": confidence, "bbox": [0, 0, 10, 10]}
    monkeypatch.setitem(ocr._engines, "vision", SimpleNamespace(name="test-confidence", run=lambda image: [line]))
    result = ocr.extract_text(FIXTURES / "notext0.png", engine="vision")
    _check_result(result)
    assert result["mean_confidence"] == confidence
    assert result["low_confidence"] is low


@pytest.mark.parametrize(
    "hypothesis, reference, expected",
    [
        pytest.param("hello world", "hello world", (0, 11, 0, 2), id="identical"),
        pytest.param("abc", "adc", (1, 3, 1, 1), id="substitution"),
        pytest.param("abxc", "abc", (1, 3, 1, 1), id="insertion"),
        pytest.param("ac", "abc", (1, 3, 1, 1), id="deletion"),
        pytest.param("one cat", "one bat", (1, 7, 1, 2), id="two-word-substitution"),
        pytest.param("one two three", "one two", (6, 7, 1, 2), id="extra-word"),
        pytest.param("", "abc def", (7, 7, 2, 2), id="empty-hypothesis"),
        pytest.param("", "", (0, 0, 0, 0), id="both-empty"),
        pytest.param("أبـشَر ١٢", "أبشر 12", (0, 7, 0, 2), id="arabic-normalization"),
    ],
)
def test_cer_wer_known_edit_counts(hypothesis, reference, expected):
    # cer_wer returns edit counts and reference lengths, not divided rates.
    assert cer_wer(hypothesis, reference) == expected
