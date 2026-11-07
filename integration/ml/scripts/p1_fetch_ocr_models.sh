#!/usr/bin/env bash
# Fetch local OCR model files once (then everything runs offline). Run from this ml/ dir.
#   Apple Vision (default on macOS): nothing to download; needs `pip install pyobjc-framework-Vision`.
#   Tesseract fallback: brew install tesseract  +  tessdata_best ara/eng below.
#   EasyOCR fallback:   pip install easyocr ; models are downloaded on first Reader() into artifacts/ocr/easyocr.
set -euo pipefail
mkdir -p artifacts/ocr/tessdata
for l in ara eng; do
  [ -f artifacts/ocr/tessdata/$l.traineddata ] || curl -sSL -o artifacts/ocr/tessdata/$l.traineddata \
    https://github.com/tesseract-ocr/tessdata_best/raw/main/$l.traineddata
done
shasum -a 256 -c - <<SUMS
ab9d157d8e38ca00e7e39c7d5363a5239e053f5b0dbdb3167dde9d8124335896  artifacts/ocr/tessdata/ara.traineddata
8280aed0782fe27257a68ea10fe7ef324ca0f8d85bd2fd145d1c2b560bcb66ba  artifacts/ocr/tessdata/eng.traineddata
SUMS
if [ "${1:-}" = "--easyocr" ]; then
  PYTHONPATH=.. .venv/bin/python -c "from ml.src.ocr import get_engine; get_engine('easyocr')"
  shasum -a 256 -c - <<SUMS
2a9afd42c374deb98aed0b53c9b77d75e1d00d4e0501f3b0276c54190c89b1a8  artifacts/ocr/easyocr/arabic.pth
4a5efbfb48b4081100544e75e1e2b57f8de3d84f213004b14b85fd4b3748db17  artifacts/ocr/easyocr/craft_mlt_25k.pth
SUMS
fi
