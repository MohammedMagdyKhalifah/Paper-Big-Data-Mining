"""Acceptance tests using Claude's actual unchanged artifacts, never substitute predictions.

Run from the integrated repository root with -c app/backend/pytest.ini.
Missing artifacts fail this suite intentionally; use -m 'not integration' for unit-only work.
"""
import csv
import hashlib
import io
import json
import socket
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.backend.main import create_app
from app.backend.schemas import AnalyzeResponse, Prediction
from app.backend.services.classifier_adapter import MockPredictor
from ml import infer

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def local_model(monkeypatch):
    monkeypatch.delenv('ML_ARTIFACT_DIR', raising=False)
    monkeypatch.delenv('APP_ML_MODE', raising=False)
    infer._reset_cache()
    yield
    infer._reset_cache()


@pytest.fixture
def real_client(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path / "real.sqlite3"}')) as client:
        yield client


@pytest.mark.parametrize('message,expected', [
    ('رمز التحقق لا يصل عند تسجيل الدخول', 'AUTH'),
    ('التطبيق بطيء', 'PERF'),
    ('شكرا التطبيق ممتاز', None),
    ('الـ OTP ما يوصلني when I try to login', None),
])
def test_actual_prediction_schema_and_sqlite(real_client, message, expected):
    response = real_client.post('/api/complaints/analyze', json={'text': message})
    assert response.status_code == 200, response.text
    result = AnalyzeResponse.model_validate(response.json())
    saved = result.message
    actual = infer.predict_text(message)
    assert saved.original_prediction.model_dump() == actual
    assert set(actual) == set(Prediction.model_fields)
    assert saved.category == expected
    assert saved.model_version == 'tfidf-baseline-v1'
    assert saved.complaint_score is not None and not saved.is_demo
    assert saved.system_name is None and saved.system_evidence == 'unknown'
    assert saved.original_event_time is None
    with real_client.app.state.engine.connect() as connection:
        row = connection.execute(text('SELECT model_version, complaint_score, is_demo FROM complaints WHERE id=:id'), {'id': saved.id}).one()
        assert row == ('tfidf-baseline-v1', actual['complaint_score'], 0)
    assert real_client.get(f'/api/complaints/{saved.id}').json()['original_prediction'] == actual
    overview = real_client.get('/api/dashboard/overview').json()
    assert overview['total_messages'] == 1
    assert overview['complaints'] == int(actual['is_complaint'])


def test_offline_startup_load_once_without_persisting(tmp_path, monkeypatch):
    def deny_network(*args, **kwargs):
        raise AssertionError('Inference must not connect to a network')
    monkeypatch.setattr(socket.socket, 'connect', deny_network)
    monkeypatch.setattr(socket, 'create_connection', deny_network)
    loads = []
    original_load = joblib.load
    def record_load(path, *args, **kwargs):
        loads.append(str(path))
        return original_load(path, *args, **kwargs)
    monkeypatch.setattr(joblib, 'load', record_load)
    with TestClient(create_app(f'sqlite:///{tmp_path / "offline.sqlite3"}')) as client:
        info = client.get('/api/models/info').json()
        assert info['mode'] == 'real' and info['status'] == 'verified'
        assert info['model_version'] == 'tfidf-baseline-v1'
        assert info['observed_versions'] == []  # Warmup is not a saved message.
        assert client.get('/api/dashboard/overview').json()['total_messages'] == 0
        loaded = infer._model
        for i in range(3):
            assert client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء', 'source_id': str(i)}).status_code == 200
        assert loaded is not None and infer._model is loaded
        assert len(loads) == 2  # Exactly one gate and one category pipeline.


@pytest.mark.parametrize('value', ['', '  \n ', None])
def test_empty_rejected_without_write(real_client, value):
    response = real_client.post('/api/complaints/analyze', json={'text': value})
    assert response.status_code == 422
    assert real_client.get('/api/complaints').json()['total'] == 0


def test_real_persistence_review_and_mock_separation(tmp_path):
    url = f'sqlite:///{tmp_path / "persistent.sqlite3"}'
    with TestClient(create_app(url, MockPredictor())) as client:
        demo = client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء'}).json()['message']
        assert demo['is_demo'] and demo['model_version'] == 'mock-v1'
    with TestClient(create_app(url)) as client:
        real = client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء'}).json()['message']
        assert real['id'] != demo['id'] and not real['is_demo']
        for extra in [{'source_id': 'DEMO-actual'}, {'is_demo': True, 'source_id': 'synthetic'}]:
            saved = client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء', **extra}).json()['message']
            assert saved['is_demo'] and saved['model_version'] == 'tfidf-baseline-v1'
        response = client.patch(f'/api/complaints/{real["id"]}/review', json={
            'is_complaint': True, 'category': 'AUTH', 'system_name': 'نظام مراجَع', 'needs_review': False})
        assert response.status_code == 200
        assert response.json()['original_prediction'] == real['original_prediction']
        assert response.json()['corrections']
    with TestClient(create_app(url)) as client:
        assert client.get('/api/dashboard/overview').json()['total_messages'] == 1
        assert client.get('/api/dashboard/overview?data_scope=demo').json()['total_messages'] == 3
        saved = client.get(f'/api/complaints/{real["id"]}').json()
        assert saved['category'] == 'AUTH' and saved['system_name'] == 'نظام مراجَع'
        assert saved['original_prediction'] == real['original_prediction']
        assert client.get(f'/api/complaints/{demo["id"]}').json()['model_version'] == 'mock-v1'


def test_repeated_csv_undated_aura_and_independent_counts(real_client):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['text', 'source_id', 'source_app', 'original_event_time'])
    # AURA-shaped verification inputs, not a new research dataset or claimed original reviews.
    writer.writerows([
        ['التطبيق بطيء', 'integration-aura-undated', 'مصدر AURA — تحقق', ''],
        ['رمز التحقق لا يصل عند تسجيل الدخول', 'dated', '', '2026-10-29T21:30:00Z'],
        ['شكرا التطبيق ممتاز', 'positive', '', ''],
        ['', 'invalid', '', ''],
    ])
    def upload():
        return real_client.post('/api/complaints/import', files={'file': ('aura-shaped-verification.csv', output.getvalue().encode('utf-8-sig'), 'text/csv')})
    first = upload().json()
    second = upload().json()
    assert (first['accepted'], first['duplicates'], first['failed']) == (3, 0, 1)
    assert (second['accepted'], second['duplicates'], second['failed']) == (0, 3, 1)
    with real_client.app.state.engine.connect() as conn:
        counts = conn.execute(text('SELECT count(*), sum(is_complaint), sum(is_complaint AND original_event_time IS NULL) FROM complaints WHERE is_demo=0')).one()
    overview = real_client.get('/api/dashboard/overview').json()
    assert (overview['total_messages'], overview['complaints']) == counts[:2] == (3, 2)
    event = real_client.get('/api/dashboard/trends?date_from=2026-10-30&date_to=2026-10-30').json()
    assert event['missing_event_time'] == counts[2] == 1
    assert event['points'] == [{'date': '2026-10-30', 'count': 1}]
    imported = real_client.get('/api/dashboard/trends?time_basis=import').json()
    assert sum(p['count'] for p in imported['points']) == 2
    assert real_client.get('/api/complaints?source=csv').json()['total'] == 3


def test_missing_model_503_diagnostics_and_no_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv('ML_ARTIFACT_DIR', str(tmp_path / 'absent'))
    with TestClient(create_app(f'sqlite:///{tmp_path / "missing.sqlite3"}')) as client:
        info = client.get('/api/models/info').json()
        assert info['mode'] == 'real' and info['status'] == 'error'
        assert info['model_version'] is None and 'FileNotFoundError' in info['integration_error']
        response = client.post('/api/complaints/analyze', json={'text': 'التطبيق بطيء'})
        assert response.status_code == 503 and 'FileNotFoundError' in response.json()['detail']
        report = client.post('/api/complaints/import', files={'file': ('test.csv', 'text\nالتطبيق بطيء\n'.encode())}).json()
        assert report['stopped'] and report['accepted'] == 0 and report['failed'] == 1
        assert client.get('/api/complaints').json()['total'] == 0
        assert client.get('/api/complaints?data_scope=demo').json()['total'] == 0


def test_delivered_artifacts_are_unchanged():
    root = Path(__file__).resolve().parents[3]
    receipt = json.loads((root / 'app/MODEL_ASSETS.json').read_text())
    for relative, expected in receipt['files'].items():
        asset = root / relative
        assert asset.stat().st_size == expected['bytes']
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == expected['sha256']


def test_actual_evaluation_report_is_displayed_verbatim(real_client, monkeypatch):
    report = Path(__file__).resolve().parents[3] / 'ml/reports/evaluation.md'
    monkeypatch.delenv('APP_EVALUATION_REPORT', raising=False)
    monkeypatch.delenv('APP_EVALUATION_MODEL_VERSION', raising=False)
    info = real_client.get('/api/models/info').json()
    assert info['evaluation_available']
    assert info['evaluation_report'] == report.read_text(encoding='utf-8')
    assert 'AI-assisted' in info['evaluation_report']
    monkeypatch.setenv('APP_EVALUATION_MODEL_VERSION', 'unrelated-model')
    assert not real_client.get('/api/models/info').json()['evaluation_available']
