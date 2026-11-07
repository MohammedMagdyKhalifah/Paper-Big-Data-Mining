import sys
from pathlib import Path

# Make `import ml` work when pytest is run from inside ml/ (mirrors PYTHONPATH=. at repo root).
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
