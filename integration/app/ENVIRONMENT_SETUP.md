# Self-contained A4 environment

## Supported, verified target

- CPython 3.12 (verified 3.12.7), macOS ARM64, macOS 14 or newer, CPU inference.
- Node 22.20 or newer compatible LTS for the existing frontend/launcher.
- Project root in the commands below means `integration/`, containing `app/` and `ml/`.
- Runtime/test packages are pinned in `backend/requirements-a4-macos-arm64-py312.lock`: 60 direct and transitive distributions, each tied to one official PyPI wheel SHA-256. `backend/a4-wheel-manifest.json` records exact filenames, URLs, sizes and hashes. Other OS/architectures need a separately reviewed target lock; do not silently substitute model-library versions.

The environment is `app/backend/.venv-a4-standalone`. It contains its own installed packages, has system/user site-packages disabled and requires no external Python package directory or PYTHONPATH/PYTHONHOME. A normal Python installation supplies the standard library, as with any virtualenv. Original model files are loaded from the repository, not downloaded at inference time.

## Fresh installation

From the integrated repository root, using the intended Python 3.12 interpreter:

```bash
unset PYTHONPATH PYTHONHOME
python3.12 -m venv app/backend/.venv-a4-standalone
app/backend/.venv-a4-standalone/bin/python -I -m pip install \
  --require-hashes --only-binary=:all: \
  -r app/backend/requirements-a4-macos-arm64-py312.lock
npm --prefix app/frontend ci
cp -n app/.env.example app/.env
```

Use a fresh virtualenv for this recipe; do not copy or symlink another environment's site-packages. The verified install used the venv's bundled pip 24.2. The old root-only requirements-a4.txt remains the source pin declaration, while the complete hash-locked file above is the reproducible installation recipe. Do not mix V1's legacy requirements.lock into this A4 environment.

On a fresh checkout, transfer the approved ignored weights before verification:

- V1: `ml/artifacts/gate.joblib` and `category.joblib`, with the tracked original manifest.
- A4: `ml/artifacts/a4/export/a4-marbert-v1/model/model.safetensors`, with the tracked full export metadata/tokenizer/config.

Use only the approved delivered weights. No training or holdout evaluation is part of setup. The V1/A4 receipts in app/MODEL_ASSETS.json and A4_MODEL_ASSETS.json preserve their hashes. Verify the original A4 checksums:

```bash
(cd ml/artifacts/a4/export/a4-marbert-v1 && shasum -a 256 -c SHA256SUMS)
app/backend/.venv-a4-standalone/bin/python -I app/backend/verify_a4_environment.py
```

The audit checks all 60 installed versions against the full lock and source pins, package/distribution origins, external path/.pth/egg-link absence, disabled system/user site, critical module imports, pip check and ten original model receipt assets. It rejects a populated PYTHONPATH/PYTHONHOME instead of using it. It neither trains nor runs evaluation.

## Offline installation

Installation needs either network access to the pinned official wheels or a previously downloaded cache. Runtime does not need internet. On a connected machine with the same target, prepare the cache:

```bash
mkdir -p app/backend/.wheelhouse-a4
app/backend/.venv-a4-standalone/bin/python -I -m pip download \
  --require-hashes --only-binary=:all: \
  -r app/backend/requirements-a4-macos-arm64-py312.lock \
  --dest app/backend/.wheelhouse-a4
```

The delivered local checkout already has all 60 verified wheels in this ignored directory (261,679,002 bytes). It is an installation cache, not a runtime dependency. To install from it into a fresh environment:

```bash
app/backend/.venv-a4-standalone/bin/python -I -m pip install \
  --no-index --find-links app/backend/.wheelhouse-a4 \
  --require-hashes --only-binary=:all: \
  -r app/backend/requirements-a4-macos-arm64-py312.lock
```

In the restricted execution environment, official wheel downloads were performed with curl, then every size/hash was verified before this same offline pip install. Normal fresh installations may use pip directly. Never bypass a hash failure; finish/re-download the affected file and verify it first.

## Configuration and startup

For an existing configuration, preserve the other settings and set:

```dotenv
APP_PYTHON=backend/.venv-a4-standalone/bin/python
APP_ML_MODE=real
ML_ARTIFACT_DIR=ml/artifacts/a4/export/a4-marbert-v1
HF_HUB_OFFLINE=1
TOKENIZERS_PARALLELISM=false
```

Remove PYTHONPATH/PYTHONHOME lines from app/.env and unset any caller exports. APP_PYTHON is relative to app/; the artifact path is relative to integration/. The Node launcher loads app/.env and waits for Backend readiness before starting Vite.

```bash
npm --prefix app run start
```

Current local ports remain frontend http://127.0.0.1:15174 and Backend http://127.0.0.1:18174/docs. A fresh .env.example uses default 5173/8000 unless optional APP_WEB_PORT/APP_API_PORT are set; choose free ports without stopping unrelated services. Ctrl+C stops the owned pair.

## V1 rollback and recovery

Stop the service, remove ML_ARTIFACT_DIR from app/.env and any exported caller value, then restart with the same standalone interpreter. V1 loads its original joblib files from ml/artifacts using packages installed in this environment; it does not require the old .venv or Claude worktree. Restore the setting and restart to re-enable A4. Stored versions and corrections are not overwritten. A running process intentionally keeps its cached model until restart.

Original environments were left untouched for recovery. The previous configuration was preserved locally at backend/storage/a4-environment-recovery/working-a4.env. That historical backup contains the old external references and is not part of normal A4/V1 setup. The old helper text was archived as legacy-pythonpath.txt. Active config and fresh-install instructions contain no external-package workaround.

## Tests

Do not load legacy PYTHONPATH helpers. From integration/:

```bash
unset PYTHONPATH PYTHONHOME
app/backend/.venv-a4-standalone/bin/python -I app/backend/verify_a4_environment.py
app/backend/.venv-a4-standalone/bin/python -E -s -m pytest \
  -c app/backend/pytest.ini app/backend/tests ml/tests -q
npm --prefix app/frontend test
npm --prefix app/frontend run build
```

Observed: 111 Python tests passed (64 Backend + all 47 unchanged ML), no skips; 18 frontend tests passed; production build passed. A further real offline process blocked networking and external package reads: A4 inference, persistence, V1 rollback and A4 re-enable all passed. Actual launcher/React/proxy startup passed on the selected standalone environment. See ENVIRONMENT_VERIFICATION.md and PROGRESS.md.
