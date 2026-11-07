"""Actual exported A4 application acceptance; no training or holdout evaluation.

Missing weights/dependencies fail intentionally. The existing V1 acceptance suite
continues to run separately with ML_ARTIFACT_DIR removed.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text

from app.backend.main import create_app
from app.backend.schemas import AnalyzeResponse, ModelInfoResponse
from app.backend.services.classifier_adapter import MockPredictor
from ml import infer

ROOT = Path(__file__).resolve().parents[3]
EXPORT = ROOT / 'ml/artifacts/a4/export/a4-marbert-v1'
VERSION = 'a4-marbert-v1'
pytestmark = [pytest.mark.integration, pytest.mark.a4]


@pytest.fixture(scope='module', autouse=True)
def a4_model():
    with pytest.MonkeyPatch.context() as env:
        env.setenv('ML_ARTIFACT_DIR', str(EXPORT))
        env.setenv('APP_ML_MODE', 'real')
        env.setenv('HF_HUB_OFFLINE', '1')
        env.setenv('TOKENIZERS_PARALLELISM', 'false')
        env.delenv('APP_EVALUATION_REPORT', raising=False)
        env.delenv('APP_EVALUATION_MODEL_VERSION', raising=False)
        infer._reset_cache()
        yield
        infer._reset_cache()


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path / "a4.sqlite3"}')) as client:
        yield client


@pytest.mark.parametrize('message,category', [
    ('رمز التحقق لا يصل عند تسجيل الدخول', 'AUTH'),
    ('الـ OTP ما يوصلني when I try to login', 'AUTH'),
    ('التطبيق بطيء', 'PERF'),
    ('الدفع fails عند تأكيد العملية', 'TRANS'),
    ('تطبيق رائع وسهل الاستخدام شكرا لكم', None),
])
def test_actual_api_predictions_match_model_and_persist(client, message, category):
    response = client.post('/api/complaints/analyze', json={'text': message})
    assert response.status_code == 200, response.text
    result = AnalyzeResponse.model_validate(response.json())
    saved = result.message
    actual = infer.predict_text(message)
    assert saved.original_prediction.model_dump() == actual
    assert saved.category == category and saved.model_version == VERSION
    assert saved.is_complaint == (category is not None)
    assert not saved.is_demo and saved.system_name is None
    assert saved.original_event_time is None
    with client.app.state.engine.connect() as db:
        assert db.execute(text('SELECT model_version, is_demo, category FROM complaints WHERE id=:id'), {'id': saved.id}).one() == (VERSION, 0, category)
    overview = client.get('/api/dashboard/overview').json()
    assert overview['total_messages'] == 1 and overview['complaints'] == int(saved.is_complaint)
    assert client.get(f'/api/complaints/{saved.id}').json()['original_prediction'] == actual


@pytest.mark.parametrize('value', ['', ' \n ', None])
def test_empty_requests_do_not_write(client, value):
    assert client.post('/api/complaints/analyze', json={'text': value}).status_code == 422
    assert client.get('/api/complaints').json()['total'] == 0


def test_report_identity_datasets_and_api_schema_unchanged(client):
    raw = client.get('/api/models/info').json()
    info = ModelInfoResponse.model_validate(raw)
    assert set(raw) == set(ModelInfoResponse.model_fields)
    assert info.status == 'verified' and info.model_version == VERSION
    assert info.evaluation_model_version == VERSION and info.evaluation_available
    assert info.evaluation_report == (ROOT / 'ml/reports/a4_model_card.md').read_text(encoding='utf-8')
    for section in ['holdout_all', 'holdout_random', 'holdout_enriched', 'holdout_codeswitch', 'external_aura_proxy', 'v1_test_NOT_BLIND', 'NON-BLIND', 'AI-assisted']:
        assert section in info.evaluation_report
    assert '| holdout_all | 1231 | 0.6896 | 0.9125 | 0.7290 |' in info.evaluation_report


def test_csv_review_restart_model_tracking_and_demo_exclusion(tmp_path):
    url = f'sqlite:///{tmp_path / "persistent.sqlite3"}'
    with TestClient(create_app(url, MockPredictor())) as client:
        assert client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء'}).json()['message']['is_demo']
    csv = 'text,source_id,source_app,original_event_time\nالتطبيق بطيء,undated,نظام تحقق,\nالـ OTP ما يوصلني when I try to login,mixed,,\nتطبيق رائع وسهل الاستخدام شكرا لكم,praise,,\n,invalid,,\n'
    with TestClient(create_app(url)) as client:
        def upload():
            return client.post('/api/complaints/import', files={'file': ('a4.csv', csv.encode('utf-8-sig'), 'text/csv')}).json()
        first, repeated = upload(), upload()
        assert (first['accepted'], first['duplicates'], first['failed']) == (3, 0, 1)
        assert (repeated['accepted'], repeated['duplicates'], repeated['failed']) == (0, 3, 1)
        records = client.get('/api/complaints').json()['items']
        assert {r['model_version'] for r in records} == {VERSION}
        saved = next(r for r in records if r['source_id'] == 'undated')
        original = saved['original_prediction']
        correction = {'is_complaint': True, 'category': 'UX', 'system_name': 'نظام مراجَع', 'needs_review': False}
        reviewed = client.patch(f'/api/complaints/{saved["id"]}/review', json=correction).json()
        assert reviewed['original_prediction'] == original and reviewed['corrections']
        assert client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء', 'source_id': 'DEMO-A4'}).json()['message']['is_demo']
        assert client.get('/api/dashboard/overview').json()['total_messages'] == 3
        assert client.get('/api/dashboard/overview?data_scope=demo').json()['total_messages'] == 2
        event = client.get('/api/dashboard/trends').json()
        assert event['points'] == [] and event['missing_event_time'] == 2
        assert sum(p['count'] for p in client.get('/api/dashboard/trends?time_basis=import').json()['points']) == 2
    with TestClient(create_app(url)) as client:
        current = client.get(f'/api/complaints/{saved["id"]}').json()
        assert current['category'] == 'UX' and current['original_prediction'] == original
        assert current['model_version'] == VERSION and current['corrections']
        with client.app.state.engine.connect() as db:
            expected = db.execute(text('SELECT count(*),sum(is_complaint) FROM complaints WHERE is_demo=0')).one()
        summary = client.get('/api/dashboard/overview').json()
        assert (summary['total_messages'], summary['complaints']) == expected == (3, 2)


def test_rollback_by_removing_setting_preserves_both_versions(tmp_path):
    url = f'sqlite:///{tmp_path / "rollback.sqlite3"}'
    with TestClient(create_app(url)) as client:
        a4 = client.post('/api/complaints/analyze', json={'text': 'الـ OTP ما يوصلني when I try to login', 'source_id': 'a4'}).json()['message']
        assert a4['model_version'] == VERSION
    with pytest.MonkeyPatch.context() as env:
        env.delenv('ML_ARTIFACT_DIR')
        infer._reset_cache()
        with TestClient(create_app(url)) as client:
            baseline = client.post('/api/complaints/analyze', json={'text': 'الـ OTP ما يوصلني when I try to login', 'source_id': 'v1'}).json()['message']
            assert baseline['model_version'] == 'tfidf-baseline-v1'
            assert client.get(f'/api/complaints/{a4["id"]}').json()['original_prediction'] == a4['original_prediction']
            assert set(client.get('/api/models/info').json()['observed_versions']) == {VERSION, 'tfidf-baseline-v1'}
            assert client.get('/api/dashboard/overview').json()['total_messages'] == 2
            assert client.get('/api/models/info').json()['evaluation_model_version'] == 'tfidf-baseline-v1'
    infer._reset_cache()


def test_missing_a4_weights_never_falls_back(tmp_path):
    missing = tmp_path / 'missing-export'
    missing.mkdir()
    (missing / 'manifest.json').write_bytes((EXPORT / 'manifest.json').read_bytes())
    with pytest.MonkeyPatch.context() as env:
        env.setenv('ML_ARTIFACT_DIR', str(missing))
        infer._reset_cache()
        with TestClient(create_app(f'sqlite:///{tmp_path / "failure.sqlite3"}')) as client:
            info = client.get('/api/models/info').json()
            assert info['mode'] == 'real' and info['status'] == 'error'
            assert info['model_version'] is None and not info['evaluation_available']
            assert client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء'}).status_code == 503
            assert client.get('/api/dashboard/overview').json()['total_messages'] == 0
    infer._reset_cache()


def test_export_hashes_and_original_v1_intact():
    for receipt_name in ['MODEL_ASSETS.json', 'A4_MODEL_ASSETS.json']:
        for relative, recorded in json.loads((ROOT / 'app' / receipt_name).read_text())['files'].items():
            path = ROOT / relative
            with path.open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == recorded['sha256']


def test_cold_offline_startup_and_api_performance(tmp_path):
    # A fresh interpreter proves there is no help from a prior process/model cache.
    script = '''
import socket,time,json,statistics,resource
def deny(*args,**kwargs): raise AssertionError('External network forbidden')
socket.socket.connect=deny
socket.create_connection=deny
from fastapi.testclient import TestClient
from app.backend.main import create_app
from ml import infer
started=time.perf_counter()
with TestClient(create_app(__DB__)) as client:
    cold=time.perf_counter()-started
    info=client.get('/api/models/info').json()
    assert info['status']=='verified' and info['model_version']=='a4-marbert-v1',info
    assert client.get('/api/complaints').json()['total']==0
    model=infer._model
    latencies=[]
    for i in range(8):
        t=time.perf_counter()
        r=client.post('/api/complaints/analyze',json={'text':'التطبيق بطيء','source_id':str(i)})
        assert r.status_code==200,r.text
        assert r.json()['message']['model_version']=='a4-marbert-v1'
        latencies.append((time.perf_counter()-t)*1000)
    assert infer._model is model
    assert client.get('/api/complaints').json()['total']==8
    print(json.dumps({'cold_start_seconds':cold,'median_analyze_ms':statistics.median(latencies),'max_analyze_ms':max(latencies),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'requests':len(latencies),'offline':True}))
'''.replace('__DB__', repr(f'sqlite:///{tmp_path / "offline.sqlite3"}'))
    env = {**os.environ, 'ML_ARTIFACT_DIR': str(EXPORT), 'HF_HUB_OFFLINE': '1', 'TOKENIZERS_PARALLELISM': 'false'}
    process = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert process.returncode == 0, process.stdout + process.stderr
    measured = json.loads(process.stdout.strip().splitlines()[-1])
    assert measured['offline'] and measured['requests'] == 8
    # Generous regression ceilings, not promises for other hardware.
    assert measured['cold_start_seconds'] < 60
    assert measured['max_analyze_ms'] < 5000
    print('A4_RUNTIME_MEASUREMENTS=' + json.dumps(measured))
