"""P1 application acceptance: real unchanged MARBERT + actual local OCR.

No training/holdout evaluation; verification inputs are not an accuracy dataset.
"""
import json
import socket
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.backend.database import Complaint, OCRDraft, P1Record, now
from app.backend.main import create_app
from app.backend.p1_schemas import OCRDraftOut, P1Response
from app.backend.services.classifier_adapter import IntegrationError, MockPredictor
from app.backend.services.p1 import P1Service
from ml import infer

ROOT=Path(__file__).resolve().parents[3]
FIXTURES=ROOT/'ml/tests/fixtures/p1'
pytestmark=pytest.mark.integration

@pytest.fixture(scope='module',autouse=True)
def a4():
    with pytest.MonkeyPatch.context() as m:
        m.setenv('ML_ARTIFACT_DIR',str(ROOT/'ml/artifacts/a4/export/a4-marbert-v1'))
        m.setenv('HF_HUB_OFFLINE','1');m.setenv('TOKENIZERS_PARALLELISM','false')
        m.setenv('APP_ML_MODE','real');infer._reset_cache()
        yield
        infer._reset_cache()

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path/"p1.sqlite3"}')) as c:yield c


def check_response(r):
    assert r.status_code==200,r.text
    result=P1Response.model_validate(r.json())
    if result.message:
        assert result.message.original_prediction.model_dump()==infer.predict_text(result.message.text_redacted)
        assert result.message.model_version=='a4-marbert-v1'
        assert result.message.p1_analysis==result.analysis.model_dump()
    a=result.analysis
    if a.systems:
        for s in a.systems.systems:
            for span in s.mentions:
                assert a.input.classified_text[span.start:span.end]==span.text
    return r.json()

@pytest.mark.parametrize('text,status,names',[
 ('تطبيق أبشر ما يفتح من أمس','identified',['أبشر']),
 ('Absher OTP ما يوصلني when I try to login','identified',['أبشر']),
 ('شكرا التطبيق ممتاز','unknown',[]),
 ('تطبيق سهل لا يعمل','unknown',[]),
 ('ابشر، توكلنا على الله','ambiguous',[]),
 ('منصة ناجز لا تعمل وتطبيق نفاذ لا يصل رمز التحقق','identified',['ناجز','نفاذ']),
])
def test_real_text_evidence_persistence_and_unknowns(client,text,status,names):
    result=check_response(client.post('/api/complaints/analyze-p1',json={'text':text}))
    assert result['analysis']['systems']['status']==status
    assert [s['name_ar'] for s in result['analysis']['systems']['systems']]==names
    saved=result['message'];assert saved['system_name']==(names[0] if len(names)==1 else None)
    assert saved['source']=='text' and saved['original_event_time'] is None
    detail=client.get(f'/api/complaints/{saved["id"]}').json()
    assert detail['p1_analysis']==result['analysis']
    repeated=client.post('/api/complaints/analyze-p1',json={'text':text}).json()
    assert repeated['duplicate'] and repeated['message']['id']==saved['id']

@pytest.mark.parametrize('body',[{}, {'text':''},{'text':' \n '},{'text':None},{'text':'x'*20001},
 {'text':'نص','corrected_text':'تغيير'}, {'text':'نص','image_ocr':{'text':'forged'}},
 {'draft_id':'not-a-uuid'}, {'draft_id':str(uuid4()),'corrected_text':' '}])
def test_invalid_request_no_write(client,body):
    assert client.post('/api/complaints/analyze-p1',json=body).status_code==422
    assert client.get('/api/complaints').json()['total']==0


def extract(client,name):
    r=client.post('/api/ocr/extract',files={'file':(name,(FIXTURES/name).read_bytes(),'image/png' if name.endswith('png') else 'image/jpeg')})
    assert r.status_code==200,r.text
    OCRDraftOut.model_validate(r.json())
    return r.json()

@pytest.mark.parametrize('name',['err00.png','chat05_degraded.jpg'])
def test_actual_ocr_review_correction_atomic_persistence_and_repeat(client,name):
    draft=extract(client,name)
    assert draft['ocr']['status']=='ok' and draft['ocr']['text']
    assert client.get('/api/complaints').json()['total']==0 # extraction never classifies/saves complaint
    corrected='تطبيق نفاذ رمز التحقق لا يصلني'
    body={'draft_id':draft['draft_id'],'corrected_text':corrected,'is_demo':True}
    result=check_response(client.post('/api/complaints/analyze-p1',json=body))
    saved=result['message'];a=result['analysis']
    assert a['ocr']['text']==draft['ocr']['text'] and a['ocr']['corrected_text']==corrected
    assert a['input']['classified_text']==corrected and saved['source']=='image'
    assert saved['system_name']=='نفاذ'
    newdraft=extract(client,name)
    repeated=client.post('/api/complaints/analyze-p1',json={**body,'draft_id':newdraft['draft_id']}).json()
    assert repeated['duplicate'] and repeated['message']['id']==saved['id']
    assert client.get('/api/dashboard/overview').json()['total_messages']==0
    assert client.get('/api/dashboard/overview?data_scope=demo&source=image').json()['total_messages']==1
    original=saved['p1_analysis']
    r=client.patch(f'/api/complaints/{saved["id"]}/review',json={'is_complaint':True,'category':'AUTH','system_name':'نظام صححه المستخدم','needs_review':False})
    assert r.status_code==200
    assert r.json()['p1_analysis']==original and r.json()['system_name']=='نظام صححه المستخدم'
    assert any(c['field_name']=='system_name' for c in r.json()['corrections'])
    with client.app.state.sessions() as db:
        assert db.scalar(select(P1Record)).result==original
        assert len(list(db.scalars(select(Complaint))))==1
    edits=client.get(f'/api/complaints/{saved["id"]}').json()['corrections']
    ocr_edits=[e for e in edits if e['field_name']=='ocr_text']
    assert len(ocr_edits)==1 and ocr_edits[0]['old_value']==draft['ocr']['text'] and ocr_edits[0]['new_value']==corrected


def test_error_signal_and_context_are_not_diagnosis(client):
    d=extract(client,'err00.png')
    r=check_response(client.post('/api/complaints/analyze-p1',json={'draft_id':d['draft_id'],'is_demo':True}))
    assert r['analysis']['analysis_kind']=='error_screen_signal'
    assert r['analysis']['signals']['needs_user_context']
    r=check_response(client.post('/api/complaints/analyze-p1',json={'draft_id':d['draft_id'],'text':'أنا أحاول أجدد الهوية ولا أستطيع','is_demo':True}))
    assert not r['analysis']['signals']['needs_user_context']


def test_blank_image_no_fake_prediction(client):
    d=extract(client,'notext0.png');assert d['ocr']['status']=='empty'
    r=check_response(client.post('/api/complaints/analyze-p1',json={'draft_id':d['draft_id']}))
    assert r['message'] is None and r['analysis']['prediction'] is None
    assert r['analysis']['analysis_kind']=='no_text'
    assert client.get('/api/complaints').json()['total']==0

@pytest.mark.parametrize('name,raw,status',[('tiny.gif',b'GIF89a',422),('bad.png',b'broken',422),('empty.jpg',b'',422),('big.jpg',b'x'*(10*1024*1024+1),413)])
def test_upload_validation(client,name,raw,status):
    assert client.post('/api/ocr/extract',files={'file':(name,raw)}).status_code==status
    assert client.get('/api/complaints').json()['total']==0


def test_missing_expired_draft_and_combined_length(client):
    assert client.post('/api/complaints/analyze-p1',json={'draft_id':str(uuid4())}).status_code==404
    d=extract(client,'err00.png')
    assert client.post('/api/complaints/analyze-p1',json={'draft_id':d['draft_id'],'text':'x'*20000}).status_code==422
    with client.app.state.sessions() as s:
        s.get(OCRDraft,d['draft_id']).expires_at=now()-timedelta(seconds=1);s.commit()
    assert client.post('/api/complaints/analyze-p1',json={'draft_id':d['draft_id']}).status_code==410


def test_real_p1_restart_offline_redaction_and_dates(tmp_path,monkeypatch):
    def deny(*args,**kwargs):raise AssertionError('network is forbidden')
    monkeypatch.setattr(socket.socket,'connect',deny);monkeypatch.setattr(socket,'create_connection',deny)
    url=f'sqlite:///{tmp_path/"restart.sqlite3"}'
    with TestClient(create_app(url)) as c:
        d=extract(c,'err00.png')
        body={'draft_id':d['draft_id'],'text':'تطبيق أبشر لا يفتح ايميلي me@example.com ورقمي 0501234567','corrected_text':'فشل تسجيل الدخول'}
        result=check_response(c.post('/api/complaints/analyze-p1',json=body));id=result['message']['id']
        assert 'me@example.com' not in json.dumps(result) and '0501234567' not in json.dumps(result)
        assert c.get('/api/dashboard/trends').json()['points']==[]
        assert c.get('/api/dashboard/trends').json()['missing_event_time']==1
        assert c.get('/api/dashboard/trends?time_basis=import').json()['points']
    with TestClient(create_app(url)) as c:
        assert c.get(f'/api/complaints/{id}').json()['p1_analysis']==result['analysis']
        assert c.post('/api/complaints/analyze-p1',json=body).json()['duplicate']


def test_mock_is_explicit_and_p1_does_not_silently_use_real(tmp_path):
    with TestClient(create_app(f'sqlite:///{tmp_path/"mock.sqlite3"}',MockPredictor())) as c:
        assert c.post('/api/complaints/analyze-p1',json={'text':'تطبيق أبشر لا يفتح'}).status_code==503
        assert c.post('/api/ocr/extract',files={'file':('x.png',b'x')}).status_code==503
        assert c.post('/api/complaints/analyze',json={'text':'التطبيق بطيء'}).json()['message']['is_demo']
        assert c.get('/api/dashboard/overview').json()['total_messages']==0


def test_explicit_ocr_and_model_error_no_write(tmp_path):
    class Broken(P1Service):
        def extract(self,raw):raise IntegrationError('OCR unavailable')
        def analyze(self,*args,**kwargs):raise IntegrationError('model unavailable')
    with TestClient(create_app(f'sqlite:///{tmp_path/"failed.sqlite3"}',p1_service=Broken())) as c:
        assert c.post('/api/ocr/extract',files={'file':('x.png',b'x')}).status_code==503
        assert c.post('/api/complaints/analyze-p1',json={'text':'التطبيق بطيء'}).status_code==503
        assert c.get('/api/complaints').json()['total']==0


def test_offline_missing_ocr_assets_fail_before_recognizer(tmp_path,monkeypatch):
    from app.backend.services.p1 import verify_ocr_assets
    monkeypatch.setenv('ML_OCR_ENGINE','tesseract')
    monkeypatch.setenv('ML_TESSDATA_DIR',str(tmp_path/'absent'))
    verify_ocr_assets.cache_clear()
    with pytest.raises(IntegrationError):P1Service().extract((FIXTURES/'err00.png').read_bytes())
    verify_ocr_assets.cache_clear()


def test_extreme_dimensions_rejected_before_ocr(client,monkeypatch):
    import struct,zlib
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',20000,20000,8,2,0,0,0))+chunk(b'IDAT',b'')+chunk(b'IEND',b'')
    monkeypatch.setenv('ML_OCR_ENGINE','missing-engine')
    assert client.post('/api/ocr/extract',files={'file':('huge.png',png)}).status_code==422
    assert client.get('/api/complaints').json()['total']==0
