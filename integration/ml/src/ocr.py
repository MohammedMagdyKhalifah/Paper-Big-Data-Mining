"""Local OCR for Arabic/English screenshots (PNG/JPEG). No cloud service, no network at run time.

    from ml.src.ocr import extract_text
    r = extract_text("screenshot.png")          # path, bytes, or PIL.Image
    r["status"]   # "ok" | "empty" (image read, no text found) | "failed" (image could not be read)

Engines (selected by name; default from ML_OCR_ENGINE or DEFAULT_ENGINE):
  * "vision":    Apple Vision framework, on-device (macOS 13+ with ar-SA). DEFAULT on macOS (best CER, light).
  * "easyocr":   EasyOCR (ar+en, CPU), models in artifacts/ocr/easyocr. DEFAULT elsewhere (portable, heavy RAM).
  * "tesseract": Tesseract 5 CLI + tessdata_best ara+eng (artifacts/ocr/tessdata). Light but inaccurate on UI text.
  Evidence: reports/p1_ocr_evaluation.md.
  * "paddle":    PaddleOCR 3.x (lang="ar"). Evaluated alternative; needs its own venv (numpy pin conflict).
A missing or misconfigured engine raises OCRUnavailableError (a deployment error, never a silent empty result).
Confidences are the engine's own recognition scores rescaled to [0, 1]; they are not calibrated probabilities.
"""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ML = Path(__file__).resolve().parents[1]
TESSDATA = Path(os.environ.get("ML_TESSDATA_DIR", ML / "artifacts/ocr/tessdata"))
EASYOCR_DIR = ML / "artifacts/ocr/easyocr"
DEFAULT_ENGINE = "vision" if sys.platform == "darwin" else "easyocr"
SUPPORTED_FORMATS = ("PNG", "JPEG")
MAX_PIXELS = 40_000_000          # refuse decompression bombs
EASYOCR_CANVAS = int(os.environ.get("ML_EASYOCR_CANVAS", 2560))  # detector max side (EasyOCR default 2560)
LOW_CONFIDENCE = 0.60            # mean line confidence below this -> low_confidence flag (review the text)

_ARABIC = re.compile(r"[؀-ۿ]")
_ALNUM = re.compile(r"[^\W_]")
_lock = threading.Lock()
_engines: dict = {}


class OCRUnavailableError(RuntimeError):
    """The requested OCR engine (binary, package or model files) is not installed locally."""


class _ImageError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def load_image(image):
    """bytes | str | Path | PIL.Image -> (RGB PIL.Image, info). Raises TypeError or _ImageError."""
    from PIL import Image, UnidentifiedImageError
    if isinstance(image, Image.Image):
        fmt = image.format or "PNG"
        im = image
    else:
        if isinstance(image, (str, Path)):
            p = Path(image)
            if not p.is_file():
                raise _ImageError("file_not_found", f"no such file: {p}")
            data = p.read_bytes()
        elif isinstance(image, (bytes, bytearray, memoryview)):
            data = bytes(image)
        else:
            raise TypeError(f"image must be a path, bytes or PIL.Image, got {type(image).__name__}")
        if not data:
            raise _ImageError("unreadable_image", "image is empty (0 bytes)")
        try:
            im = Image.open(io.BytesIO(data))
            fmt = im.format
            if fmt not in SUPPORTED_FORMATS:
                raise _ImageError("unsupported_format", f"format {fmt!r} not supported; use PNG or JPEG")
            if im.width * im.height > MAX_PIXELS:
                raise _ImageError("unreadable_image", f"image too large ({im.width}x{im.height})")
            im.load()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as e:
            raise _ImageError("unreadable_image", f"cannot decode image: {e}") from None
    if fmt not in SUPPORTED_FORMATS:
        raise _ImageError("unsupported_format", f"format {fmt!r} not supported; use PNG or JPEG")
    from PIL import ImageOps
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB"), {"format": fmt, "width": im.width, "height": im.height}


def _order_lines(items):
    """items: [(text, conf, (x0, y0, x1, y1))] word/segment boxes -> lines in reading order.
    Rows by vertical overlap, top to bottom; inside a row right-to-left if the row has Arabic, else left-to-right."""
    rows = []
    for t, c, b in sorted(items, key=lambda it: (it[2][1] + it[2][3]) / 2):
        cy, h = (b[1] + b[3]) / 2, b[3] - b[1]
        for r in rows:
            if abs(r["cy"] - cy) <= 0.5 * max(h, r["h"]):
                r["items"].append((t, c, b))
                break
        else:
            rows.append({"cy": cy, "h": h, "items": [(t, c, b)]})
    lines = []
    for r in rows:
        rtl = any(_ARABIC.search(t) for t, _, _ in r["items"])
        its = sorted(r["items"], key=lambda it: -it[2][2] if rtl else it[2][0])
        confs = [c for _, c, _ in its if c is not None]
        bx = [it[2] for it in its]
        lines.append({"text": " ".join(t for t, _, _ in its).strip(),
                      "confidence": round(sum(confs) / len(confs), 4) if confs else None,
                      "bbox": [int(min(b[0] for b in bx)), int(min(b[1] for b in bx)),
                               int(max(b[2] for b in bx)), int(max(b[3] for b in bx))]})
    return [l for l in lines if l["text"]]


class TesseractEngine:
    def __init__(self):
        self.bin = shutil.which("tesseract") or "/opt/homebrew/bin/tesseract"
        if not Path(self.bin).exists():
            raise OCRUnavailableError("tesseract binary not found (macOS: brew install tesseract)")
        for lang in ("ara", "eng"):
            if not (TESSDATA / f"{lang}.traineddata").is_file():
                raise OCRUnavailableError(f"missing {TESSDATA / (lang + '.traineddata')} (run scripts/p1_fetch_ocr_models.sh)")
        v = subprocess.run([self.bin, "--version"], capture_output=True, text=True).stdout.split()[1]
        self.name = f"tesseract-{v}/ara+eng/tessdata_best"

    @staticmethod
    def _prep(im):
        """Grayscale, invert dark themes, upscale small screenshots (Tesseract prefers ~30px x-height)."""
        from PIL import ImageOps, ImageStat
        g = ImageOps.grayscale(im)
        if ImageStat.Stat(g).mean[0] < 110:
            g = ImageOps.invert(g)
        scale = 2.0 if g.width < 1000 else 1.0
        if scale != 1.0:
            g = g.resize((int(g.width * scale), int(g.height * scale)))
        return g, scale

    def run(self, im):
        g, scale = self._prep(im)
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.png"
            g.save(src)
            r = subprocess.run([self.bin, str(src), str(Path(d) / "out"), "--tessdata-dir", str(TESSDATA),
                                "-l", "ara+eng", "--psm", "3", "-c", "tessedit_create_tsv=1", "-c", "tessedit_create_txt=0"], capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip()[-300:])
            rows = (Path(d) / "out.tsv").read_text(encoding="utf-8").splitlines()[1:]
        lines, cur = [], {}
        for row in rows:
            f = row.split("\t")
            if len(f) < 12 or f[0] != "5" or not f[11].strip():
                continue
            key = (f[2], f[3], f[4])                      # block, paragraph, line
            x, y, w, h = (int(v) / scale for v in f[6:10])
            cur.setdefault(key, []).append((f[11].strip(), max(float(f[10]), 0.0) / 100.0, (x, y, x + w, y + h)))
        for key in sorted(cur, key=lambda k: tuple(int(v) for v in k)):
            ws = cur[key]                                  # tesseract emits words in reading (logical) order
            bx = [b for _, _, b in ws]
            lines.append({"text": " ".join(t for t, _, _ in ws), "confidence": round(sum(c for _, c, _ in ws) / len(ws), 4),
                          "bbox": [int(min(b[0] for b in bx)), int(min(b[1] for b in bx)),
                                   int(max(b[2] for b in bx)), int(max(b[3] for b in bx))]})
        return lines


class EasyOCREngine:
    def __init__(self):
        try:
            import easyocr
        except ImportError as e:
            raise OCRUnavailableError("easyocr not installed") from e
        EASYOCR_DIR.mkdir(parents=True, exist_ok=True)
        self.reader = easyocr.Reader(["ar", "en"], gpu=False, model_storage_directory=str(EASYOCR_DIR), verbose=False)
        self.name = f"easyocr-{easyocr.__version__}/ar+en/canvas{EASYOCR_CANVAS}"

    def run(self, im):
        import numpy as np
        res = self.reader.readtext(np.array(im), detail=1, paragraph=False, canvas_size=EASYOCR_CANVAS)
        items = [(t, float(c), (min(p[0] for p in box), min(p[1] for p in box), max(p[0] for p in box), max(p[1] for p in box)))
                 for box, t, c in res if t.strip()]
        return _order_lines(items)


class PaddleEngine:
    def __init__(self):
        try:
            import paddleocr
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise OCRUnavailableError("paddleocr not installed (use .venv-paddle)") from e
        self.ocr = PaddleOCR(lang="ar", use_doc_orientation_classify=False, use_doc_unwarping=False,
                             use_textline_orientation=False)
        self.name = f"paddleocr-{paddleocr.__version__}/ar"

    def run(self, im):
        import numpy as np
        out = self.ocr.predict(np.array(im)[:, :, ::-1])
        items = []
        for page in out:
            for t, c, poly in zip(page["rec_texts"], page["rec_scores"], page["rec_polys"]):
                if t.strip():
                    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
                    items.append((t, float(c), (min(xs), min(ys), max(xs), max(ys))))
        return _order_lines(items)


class VisionEngine:
    """Apple Vision framework (VNRecognizeTextRequest, accurate level, ar-SA + en-US), on-device. macOS only."""

    def __init__(self):
        try:
            import Quartz
            import Vision
        except ImportError as e:
            raise OCRUnavailableError("Apple Vision OCR needs macOS + pyobjc-framework-Vision") from e
        self.Vision, self.Quartz = Vision, Quartz
        req = Vision.VNRecognizeTextRequest.alloc().init()
        langs, _ = req.supportedRecognitionLanguagesAndReturnError_(None)
        if "ar-SA" not in list(langs or []):
            raise OCRUnavailableError("this macOS version's Vision framework has no Arabic text recognition")
        import platform
        self.name = f"apple-vision/macOS-{platform.mac_ver()[0]}/ar-SA+en-US/accurate"

    def run(self, im):
        V, Q = self.Vision, self.Quartz
        from Foundation import NSData
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        data = buf.getvalue()
        src = Q.CGImageSourceCreateWithData(NSData.dataWithBytes_length_(data, len(data)), None)
        cg = Q.CGImageSourceCreateImageAtIndex(src, 0, None)
        req = V.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(V.VNRequestTextRecognitionLevelAccurate)
        req.setRecognitionLanguages_(["ar-SA", "en-US"])
        req.setUsesLanguageCorrection_(True)
        handler = V.VNImageRequestHandler.alloc().initWithCGImage_options_(cg, None)
        ok, err = handler.performRequests_error_([req], None)
        if not ok:
            raise RuntimeError(f"Vision request failed: {err} (sandboxed processes may lack Vision access; set ML_OCR_ENGINE=easyocr)")
        W, H = im.width, im.height
        items = []
        for obs in req.results() or []:
            cand = obs.topCandidates_(1)
            if not cand:
                continue
            t, c = str(cand[0].string()), float(cand[0].confidence())
            bb = obs.boundingBox()                         # normalised, origin bottom-left
            x0, y1 = bb.origin.x * W, (1 - bb.origin.y) * H
            x1, y0 = x0 + bb.size.width * W, y1 - bb.size.height * H
            if t.strip():
                items.append((t, c, (x0, y0, x1, y1)))
        return _order_lines(items)


_ENGINES = {"tesseract": TesseractEngine, "easyocr": EasyOCREngine, "paddle": PaddleEngine, "vision": VisionEngine}


def get_engine(name=None):
    name = name or os.environ.get("ML_OCR_ENGINE", DEFAULT_ENGINE)
    if name not in _ENGINES:
        raise ValueError(f"unknown OCR engine {name!r}; choose from {sorted(_ENGINES)}")
    with _lock:
        if name not in _engines:
            _engines[name] = _ENGINES[name]()
    return _engines[name]


def extract_text(image, *, engine: str | None = None) -> dict:
    """OCR one PNG/JPEG image. Never raises for a bad image (status "failed" + error code); raises TypeError for a
    wrong argument type and OCRUnavailableError if the engine is not installed."""
    t0 = time.perf_counter()
    eng = get_engine(engine)
    out = {"status": None, "text": "", "lines": [], "mean_confidence": None, "low_confidence": False,
           "error": None, "engine": eng.name, "image": None, "elapsed_ms": None}
    try:
        im, info = load_image(image)
        out["image"] = info
        lines = eng.run(im)
    except _ImageError as e:
        out.update(status="failed", error={"code": e.code, "message": str(e)})
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
        out.update(status="failed", error={"code": "engine_error", "message": str(e)[:300]})
    else:
        # a line with no letter/digit (e.g. "*****" read from star icons) is not readable text
        lines = [l for l in lines if _ALNUM.search(l["text"])]
        out["lines"] = lines
        out["text"] = "\n".join(l["text"] for l in lines)
        confs = [l["confidence"] for l in lines if l["confidence"] is not None]
        out["mean_confidence"] = round(sum(confs) / len(confs), 4) if confs else None
        out["low_confidence"] = out["mean_confidence"] is not None and out["mean_confidence"] < LOW_CONFIDENCE
        out["status"] = "ok" if out["text"].strip() else "empty"
    out["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out
