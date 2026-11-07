# Standalone A4 environment verification — 2026-10-30

Scope: environment packaging/reproducibility only. No model, evaluation dataset/report, API contract, database schema or website feature was changed. The verified A4 integration and V1 rollback branch remain preserved.

## Installation provenance

- Fresh candidate app/backend/.venv-a4-standalone, include-system-site-packages=false; original environments/config retained until candidate passed.
- Exact working-compatible direct/transitive closure: 60 packages. All Claude A4 core pins and app Backend pins unchanged. New complete CPython 3.12/macOS ARM64 lock contains every version plus the SHA-256 of its selected official wheel; manifest records official PyPI URLs/filenames/sizes.
- All 60 release metadata requests/downloads succeeded. Wheel bytes total 261,679,002. Fresh wheel downloads avoided the previous package-copy/cloud-file read stalls.
- One early candidate attempt happened while Torch was still downloading. Size/hash verification and pip hash enforcement rejected it before installation; old setup untouched. After completion all wheel SHA-256 values matched, and a fresh --no-index --require-hashes --only-binary pip install succeeded.
- A project-local ignored .wheelhouse-a4 contains those verified wheels for offline reinstall. The runtime imports no files from this cache or download scratch.

## Isolation evidence

Operational verify_a4_environment.py passed under both Python -I and ordinary interpreter startup. All 60 installed distributions and 15 critical module origins resolve inside the new environment. It also checked all loaded third-party submodule origins, no external sys.path site/dist-packages, no external .pth/egg links, no PYTHONPATH/PYTHONHOME, user/system site disabled, source pins/full lock agreement and pip check.

A negative test injected a fake external PYTHONPATH; the audit rejected it before importing dependencies. No sys.path/registration workaround was added to application code. The active .env now selects the standalone interpreter and contains no Python path override. Original environments are recovery-only, not dependencies of either A4 or V1 operation.

## Model assets and offline execution

- Original A4 SHA256SUMS: all 6 files matched, including safetensors.
- V1/A4 receipts: all 10 file sizes/hashes matched. Training code, exports and evaluation records unchanged.
- An extra clean subprocess denied all socket/DNS calls and all reads from any external site/dist-packages. Network attempts=[]; external package reads=[].
- A4 cold app startup: 6.1068s in this separate execution probe. Actual Arabic AUTH, mixed AUTH, praise/noncomplaint, PERF and mixed TRANS scores matched the prior verified outputs.
- Five A4 messages saved in temporary SQLite, V1 selected by removing ML_ARTIFACT_DIR and restarting factory/cache, V1 mixed input noncomplaint 0.3165 saved, then A4 re-enabled with all six records and both versions retained.
- No production database write from these probes. These are execution checks, not a rerun of holdout evaluation or a new research dataset.

## Executed acceptance checks

| Check | Observed outcome |
| --- | --- |
| Candidate python -I backend/verify_a4_environment.py | Passed; 60 pinned local distributions, 15 critical modules, 10 model assets; pip check clean |
| Same audit without isolated-mode flags | Passed; ordinary startup also has no external package paths |
| Candidate python -E -s -m pytest -c app/backend/pytest.ini app/backend/tests ml/tests -q | 111 passed in 21.47s; 64 Backend + all 47 unchanged ML; no skips |
| npm --prefix app/frontend test | 18 passed in 1.92s |
| npm --prefix app/frontend run build | TypeScript/Vite passed, 2308 modules, Vite 229ms; bundle identities unchanged |
| Real offline application/rollback probe | A4, V1 and A4 re-enable passed; zero networking/external package reads |
| Actual npm launcher, selected new interpreter | A4 loaded → Backend diagnostics 200 → Vite ready; no startup failure |
| Live React HTML + Vite API proxy | HTTP success; a4-marbert-v1 verified, exact original report; normal real overview remains 0 messages |

Existing non-failing warnings: Starlette's deprecated AnyIO BlockingPortal alias under these pinned versions; Torch's macOS distributed redirect note. No new compatibility blocker was found. The same existing Torch resource_tracker cleanup warning may appear on shutdown; it does not prevent restart.

## Preservation and recovery

Active settings switch happened only after install/audit/full tests/offline acceptance passed. Prior working .env is retained in ignored recovery storage; original A4 and V1 environments and source worktrees were not overwritten. Existing unrelated frontend/node_modules 2 link untouched. No unrelated services stopped.

Normal SQLite remains the original nine Demo messages, with no real verification submissions. The dedicated earlier execution archives remain separate. The standalone environment is created at its final path rather than moved, preserving generated executable shebangs. It can be reproduced from the hashed target lock using online pip or the verified offline wheel cache; no original ML worktree package directory is required.
