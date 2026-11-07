"""Audit the installed A4 environment and original model assets without inference.

Run with the project environment's Python -I. No external package paths, package
installation, model training, or evaluation is performed by this command.
"""
from importlib import import_module, metadata
import hashlib
import json
import os
from pathlib import Path
import site
import subprocess
import sys

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parents[1]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def canonical(name):
    return name.lower().replace('_', '-').replace('.', '-')


def verify(profile='a4'):
    prefix = Path(sys.prefix).resolve()
    require(sys.prefix != sys.base_prefix, 'Use an isolated project virtualenv.')
    require(prefix.is_relative_to(BACKEND), 'Virtualenv must be inside app/backend/.')
    require(not os.environ.get('PYTHONPATH'), 'Unset PYTHONPATH; external package references are forbidden.')
    require(not os.environ.get('PYTHONHOME'), 'Unset PYTHONHOME for the project environment.')
    require(site.ENABLE_USER_SITE is False, 'User site-packages must be disabled.')
    config = (prefix / 'pyvenv.cfg').read_text().lower()
    require('include-system-site-packages = false' in config, 'System site-packages must be disabled.')
    for entry in sys.path:
        path = Path(entry).resolve()
        if 'site-packages' in path.parts or 'dist-packages' in path.parts:
            require(path.is_relative_to(prefix), f'External site-packages on sys.path: {path}')
    for directory in site.getsitepackages():
        for file in Path(directory).glob('*.pth'):
            for line in file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith(('#', 'import ', 'import\t')):
                    target = (file.parent / line).resolve()
                    require(target.is_relative_to(prefix), f'External .pth reference: {file}: {target}')
        require(not list(Path(directory).glob('*.egg-link')), 'Editable external package links are forbidden.')
    require(profile in {'a4','p1','p1-easyocr'}, 'Unknown environment profile.')
    manifest = json.loads((BACKEND / f'{profile}-wheel-manifest.json').read_text())
    wheels = manifest['wheels']
    lock = (BACKEND / f'requirements-{profile}-macos-arm64-py312.lock').read_text()
    entries = [line.strip() for line in lock.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    expected_entries = {f"{row['name']}=={row['version']} --hash=sha256:{row['sha256']}" for row in wheels}
    require(len(entries) == len(wheels) and set(entries) == expected_entries, 'Lock/manifest entries differ.')
    for row in wheels:
        expected = f"{row['name']}=={row['version']} --hash=sha256:{row['sha256']}"
        require(expected in lock.splitlines(), f'Lock/manifest mismatch: {row["name"]}')
        package = metadata.distribution(row['name'])
        require(package.version == row['version'], f'Wrong installed version: {row["name"]}={package.version}')
        require(Path(package.locate_file('')).resolve().is_relative_to(prefix), f'External distribution: {row["name"]}')
    for package in metadata.distributions():
        require(Path(package.locate_file('')).resolve().is_relative_to(prefix), f'External installed package: {package.metadata["Name"]}')
    for relative in ['../../ml/requirements-a4-inference.txt', 'requirements-a4.txt']:
        for line in (BACKEND / relative).read_text().splitlines():
            if line and not line.startswith(('#', '-')):
                name, version = line.split('==')
                require(metadata.version(name) == version, f'Required pin mismatch: {name}')
                require(any(canonical(row['name']) == canonical(name) and row['version'] == version for row in wheels), f'Pin missing from lock: {name}')
    modules = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 'httpx', 'numpy', 'scipy', 'pandas',
               'pyarrow', 'joblib', 'sklearn', 'torch', 'transformers', 'tokenizers', 'safetensors']
    if profile.startswith('p1'): modules += ['PIL','objc','Foundation','Quartz','CoreML','Vision']
    if profile=='p1-easyocr': modules += ['easyocr','torchvision','cv2','skimage']
    for name in modules:
        module = import_module(name)
        require(Path(module.__file__).resolve().is_relative_to(prefix), f'External module origin: {name}')
    for name, module in tuple(sys.modules.items()):
        origin = getattr(module, '__file__', None)
        if origin and ('site-packages' in Path(origin).parts or 'dist-packages' in Path(origin).parts):
            require(Path(origin).resolve().is_relative_to(prefix), f'External imported submodule: {name}')
    files = 0
    for receipt in ['MODEL_ASSETS.json', 'A4_MODEL_ASSETS.json']:
        for relative, expected in json.loads((ROOT / 'app' / receipt).read_text())['files'].items():
            path = ROOT / relative
            require(path.stat().st_size == expected['bytes'], f'Model asset size mismatch: {relative}')
            with path.open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == expected['sha256'], f'Model checksum mismatch: {relative}')
            files += 1
    check = subprocess.run([sys.executable, '-I', '-m', 'pip', 'check'], capture_output=True, text=True)
    require(check.returncode == 0, check.stdout.strip() or check.stderr.strip())
    ocr_files=0
    if profile=='p1-easyocr':
        for relative,expected in json.loads((ROOT/'app/P1_OCR_ASSETS.json').read_text())['files'].items():
            if '/easyocr/' not in relative: continue
            with (ROOT/relative).open('rb') as stream:
                require(hashlib.file_digest(stream,'sha256').hexdigest()==expected, f'OCR checksum mismatch: {relative}')
            ocr_files+=1
    return {'environment': str(prefix), 'pinned_distributions': len(wheels), 'checked_modules': modules,
            'model_assets_verified': files, 'ocr_assets_verified':ocr_files, 'external_site_packages': [], 'pythonpath': None,
            'system_site_packages': False, 'user_site_packages': False, 'pip_check': check.stdout.strip()}


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',choices=['a4','p1','p1-easyocr'],default='a4')
    try:
        print(json.dumps(verify(parser.parse_args().profile), indent=2))
    except (OSError, RuntimeError, ImportError) as error:
        raise SystemExit(f'A4 environment verification failed: {error}')
