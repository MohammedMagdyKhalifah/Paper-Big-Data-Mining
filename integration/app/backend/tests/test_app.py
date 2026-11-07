import builtins
import csv
import io
from datetime import datetime, timezone
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from app.backend.main import create_app
from app.backend.database import Complaint
from app.backend.schemas import Prediction
from app.backend.services.classifier_adapter import IntegrationError, MockPredictor, RealPredictor

@pytest.fixture
def client(tmp_path):
    api=create_app(f'sqlite:///{tmp_path / "test.sqlite3"}',MockPredictor())
    with TestClient(api) as c: yield c


def analyze(client,text='التطبيق بطيء',**extra):
    response=client.post('/api/complaints/analyze',json={'text':text,**extra})
    assert response.status_code==200,response.text
    return response.json()['message']


def upload(client,rows):
    output=io.StringIO();writer=csv.DictWriter(output,fieldnames=['text','source_id','source_app','original_event_time','ignored'])
    writer.writeheader();writer.writerows(rows)
    return client.post('/api/complaints/import',files={'file':('test.csv',output.getvalue().encode('utf-8-sig'),'text/csv')})


def test_mock_contract_and_no_ml_import(monkeypatch):
    original=builtins.__import__
    def guard(name,*args,**kwargs):
        assert not name.startswith('ml')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guard)
    result=MockPredictor().predict('التطبيق بطيء')
    assert set(result.model_dump())=={'is_complaint','complaint_score','category','category_score','needs_review','model_version'}
    assert result.category=='PERF' and result.category_score is None
    with pytest.raises(ValueError): MockPredictor().predict('  ')

@pytest.mark.parametrize('key,value',[('is_complaint','yes'),('needs_review',1),('complaint_score',True),('category_score',float('nan')),('category_score',1.1),('category','FAKE'),('model_version',' ')])
def test_real_rejects_invalid_contract(key,value):
    data=MockPredictor().predict('التطبيق بطيء').model_dump();data[key]=value
    with pytest.raises(IntegrationError): RealPredictor(lambda _:data).predict('التطبيق بطيء')


def test_real_missing_module_fails_without_fallback(client,monkeypatch):
    def fail(_): raise ModuleNotFoundError('missing ml model')
    monkeypatch.setattr('app.backend.services.classifier_adapter.import_module',fail)
    client.app.state.predictor.mode='mock'  # Existing Mock remains entirely isolated.
    predictor=RealPredictor()
    with pytest.raises(IntegrationError,match='missing ml model'): predictor.predict('التطبيق بطيء')
    assert predictor.last_version is None


def test_real_success(tmp_path):
    data={'is_complaint':True,'complaint_score':None,'category':'AUTH','category_score':None,'needs_review':True,'model_version':'test-adapter-v1'}
    api=create_app(f'sqlite:///{tmp_path / "real.sqlite3"}',RealPredictor(lambda _:data))
    with TestClient(api) as c:
        m=analyze(c)
        assert not m['is_demo'] and m['category']=='AUTH'
        assert c.get('/api/dashboard/overview').json()['complaints']==1
        assert c.get('/api/models/info').json()['status']=='verified'


def test_real_api_error_is_503_and_no_record(tmp_path):
    def fail(_): raise FileNotFoundError('weights missing')
    api=create_app(f'sqlite:///{tmp_path / "real.sqlite3"}',RealPredictor(fail))
    with TestClient(api) as c:
        result=c.post('/api/complaints/analyze',json={'text':'test'})
        assert result.status_code==503 and 'weights missing' in result.json()['detail']
        assert c.get('/api/complaints').json()['total']==0

@pytest.mark.parametrize('payload',[{'text':''},{'text':'  '},{'text':'x'*20001},{'text':'a','original_event_time':'bad date'}])
def test_input_validation(client,payload):
    assert client.post('/api/complaints/analyze',json=payload).status_code==422


def test_no_raw_pii_saved_or_echoed(client):
    m=analyze(client,'هاتف 0501234567 وبريد person@example.com وهوية 1234567890')
    assert '0501234567' not in m['text_redacted']
    assert 'person@example.com' not in m['text_redacted']
    assert '1234567890' not in m['text_redacted']
    result=client.post('/api/complaints/analyze',json={'text':'sensitive','original_event_time':'bad'})
    assert 'sensitive' not in result.text


def test_csv_partial_and_reimport(client):
    rows=[{'text':'التطبيق بطيء','source_id':'a','source_app':'نظام ألف'},{'text':' ','source_id':'b'},{'text':'test','original_event_time':'nope'}]
    first=upload(client,rows).json()
    assert (first['accepted'],first['failed'],first['duplicates'])==(1,2,0)
    assert first['errors'][0]['row']==3
    assert upload(client,rows).json()['duplicates']==1
    assert client.get('/api/complaints?data_scope=demo').json()['total']==1


def test_duplicate_and_independent_ids(client):
    first=analyze(client,source_id='one')
    assert analyze(client,source_id='one')['id']==first['id']
    assert analyze(client,source_id='two')['id']!=first['id']
    assert analyze(client,'نص قريب') ['id'] != analyze(client,'نص قريب جدا')['id']


def test_noncomplaint_and_demo_separation(client):
    analyze(client);m=analyze(client,'شكرا التطبيق ممتاز')
    assert not m['is_complaint'] and m['category'] is None
    assert client.get('/api/dashboard/overview').json()['total_messages']==0
    result=client.get('/api/dashboard/overview?data_scope=demo').json()
    assert result['total_messages']==2 and result['complaints']==1
    assert sum(x['count'] for x in result['categories'])==1
    assert result['complaint_ratio']==.5


def test_missing_event_and_riyadh_boundary(client):
    m=analyze(client,source_id='missing')
    assert m['original_event_time'] is None
    analyze(client,source_id='dated',original_event_time='2026-10-29T21:30:00Z')
    result=client.get('/api/dashboard/trends?data_scope=demo&date_from=2026-10-30&date_to=2026-10-30').json()
    assert result['points']==[{'date':'2026-10-30','count':1}]
    assert result['missing_event_time']==1
    assert client.get('/api/dashboard/trends?data_scope=demo&time_basis=import').json()['points']
    m=analyze(client,source_id='naive',original_event_time='2026-10-30T00:30:00')
    assert m['original_event_time'].startswith('2026-10-29T21:30:00')


def test_review_retains_original_and_updates_counts(client):
    m=analyze(client,source_app='نظام ألف')
    patch={'is_complaint':False,'category':'AUTH','system_name':'نظام باء','needs_review':False}
    response=client.patch(f'/api/complaints/{m["id"]}/review',json=patch)
    assert response.status_code==200,response.text
    current=response.json()
    assert current['category'] is None and current['original_prediction']['category']=='PERF'
    assert current['original_system_name']=='نظام ألف' and current['system_reviewed']
    assert len(current['corrections'])==4
    assert client.get('/api/dashboard/overview?data_scope=demo').json()['complaints']==0
    assert client.get('/api/systems?data_scope=demo').json()['items']==[]
    assert len(client.patch(f'/api/complaints/{m["id"]}/review',json=patch).json()['corrections'])==4


def test_independent_sql_counts_filters_and_pagination(client):
    for i in range(23): analyze(client,source_id=str(i),source_app='ألف' if i%2 else 'باء')
    result=client.get('/api/complaints?data_scope=demo&page=2&page_size=20').json()
    assert len(result['items'])==3 and result['total']==23
    with client.app.state.engine.connect() as conn:
        expected=conn.execute(text('SELECT count(*) FROM complaints WHERE is_demo=1 AND is_complaint=1')).scalar()
    assert client.get('/api/dashboard/overview?data_scope=demo').json()['complaints']==expected
    groups=client.get('/api/systems?data_scope=demo').json()
    assert sum(s['count'] for s in groups['items'])==23
    assert abs(sum(s['share'] for s in groups['items'])-1)<1e-9
    assert client.get('/api/complaints?data_scope=demo&system=ألف').json()['total']==11
    assert client.get('/api/complaints?data_scope=demo&category=AUTH').json()['total']==0
    assert client.get('/api/complaints?data_scope=demo&q=بطيء').json()['total']==23
    assert client.get('/api/complaints?data_scope=demo&q=%25').json()['total']==0


def test_persistence(tmp_path):
    url=f'sqlite:///{tmp_path / "persist.sqlite3"}'
    with TestClient(create_app(url,MockPredictor())) as c: analyze(c)
    with TestClient(create_app(url,MockPredictor())) as c:
        assert c.get('/api/complaints?data_scope=demo').json()['total']==1

@pytest.mark.parametrize('raw',[b'other\nno text\n',b'text,text\na,b\n',b'\xff\xfe'])
def test_bad_csv(client,raw):
    assert client.post('/api/complaints/import',files={'file':('bad.csv',raw)}).status_code==422


def test_oversize_csv(client):
    assert client.post('/api/complaints/import',files={'file':('big.csv',b'x'*(10*1024*1024+1))}).status_code==413


def test_import_real_failure_stops_after_partial_progress(tmp_path):
    p=MockPredictor().predict('التطبيق بطيء').model_dump();p['model_version']='test-real'
    def predict(value):
        if value=='fail': raise FileNotFoundError('weights unavailable')
        return p
    with TestClient(create_app(f'sqlite:///{tmp_path / "partial.sqlite3"}',RealPredictor(predict))) as c:
        result=upload(c,[{'text':'good'},{'text':'fail'},{'text':'later'}]).json()
        assert result['accepted']==1 and result['failed']==1 and result['processed']==2 and result['stopped']


def test_errors_and_model_info(client):
    assert client.get('/api/complaints/999').status_code==404
    assert client.get('/api/complaints?page=0').status_code==422
    assert client.get('/api/dashboard/overview?date_from=2026-10-30&date_to=2026-10-01').status_code==422
    info=client.get('/api/models/info').json()
    assert info['mode']=='mock' and not info['evaluation_available']
    assert info['evaluation_report'] is None


def test_documented_response_schemas(client):
    schema=client.get('/openapi.json').json()
    expected={'/api/dashboard/overview':'OverviewResponse','/api/dashboard/trends':'TrendsResponse',
              '/api/systems':'SystemsResponse','/api/models/info':'ModelInfoResponse'}
    for path,name in expected.items():
        response=schema['paths'][path]['get']['responses']['200']['content']['application/json']['schema']
        assert response['$ref'].endswith('/'+name)


def test_unknown_system_and_noncomplaint_filter(client):
    analyze(client,source_id='unknown')
    analyze(client,'شكرا التطبيق ممتاز',source_id='positive')
    assert client.get('/api/complaints?data_scope=demo&system=__unknown__').json()['total']==2
    assert client.get('/api/complaints?data_scope=demo&is_complaint=false').json()['total']==1
    systems=client.get('/api/systems?data_scope=demo').json()['items']
    assert systems==[{'name':None,'count':1,'share':1.0,'categories':{'PERF':1}}]


def test_week_month_aggregation(client):
    for id,date in [('a','2026-10-29T10:00:00Z'),('b','2026-10-30T10:00:00Z')]:
        analyze(client,source_id=id,original_event_time=date)
    assert client.get('/api/dashboard/trends?data_scope=demo&interval=week').json()['points']==[{'date':'2026-10-26','count':2}]
    assert client.get('/api/dashboard/trends?data_scope=demo&interval=month').json()['points']==[{'date':'2026-10-01','count':2}]


def test_evaluation_report_requires_matching_observed_real_version(tmp_path,monkeypatch):
    report=tmp_path/'evaluation.md';report.write_text('An actual source report for test injection only.')
    monkeypatch.setenv('APP_EVALUATION_REPORT',str(report))
    monkeypatch.setenv('APP_EVALUATION_MODEL_VERSION','test-version')
    prediction=MockPredictor().predict('التطبيق بطيء').model_dump();prediction['model_version']='test-version'
    with TestClient(create_app(f'sqlite:///{tmp_path / "report.sqlite3"}',RealPredictor(lambda _:prediction))) as c:
        assert not c.get('/api/models/info').json()['evaluation_available']
        analyze(c)
        assert c.get('/api/models/info').json()['evaluation_report']==report.read_text()
        monkeypatch.setenv('APP_EVALUATION_MODEL_VERSION','wrong-version')
        assert not c.get('/api/models/info').json()['evaluation_available']


def test_mock_cannot_be_marked_real_and_synthetic_real_predictions_excluded(client,tmp_path):
    m=analyze(client,is_demo=False)
    assert m['is_demo']
    p=MockPredictor().predict('التطبيق بطيء').model_dump();p['model_version']='test-real'
    with TestClient(create_app(f'sqlite:///{tmp_path / "synthetic.sqlite3"}',RealPredictor(lambda _:p))) as c:
        assert analyze(c,source_id='DEMO-001')['is_demo']
        assert analyze(c,source_id='synthetic',is_demo=True)['is_demo']
        assert not analyze(c,source_id='actual')['is_demo']
        assert c.get('/api/dashboard/overview').json()['total_messages']==1
        assert c.get('/api/dashboard/overview?data_scope=demo').json()['total_messages']==2


def test_overview_completeness_and_source_mix_from_sql(client):
    first=analyze(client,source_id='quality-1',source_app='نظام ألف',original_event_time='2026-10-29T10:00:00Z')
    analyze(client,source_id='quality-2')
    analyze(client,'شكرا التطبيق ممتاز',source_id='quality-3',source_app='نظام باء')
    upload(client,[{'text':'التطبيق بطيء','source_id':'quality-4','source_app':'نظام جيم'}])
    client.patch(f'/api/complaints/{first["id"]}/review',json={'is_complaint':True,'category':'PERF','system_name':'نظام ألف','needs_review':False})
    info=client.get('/api/dashboard/overview?data_scope=demo').json()
    assert info['total_messages']==4 and info['complaints']==3
    assert info['no_review_required_messages']==1 and info['known_system_complaints']==2 and info['dated_complaints']==1
    assert info['comparison'] is None
    assert info['sources']==[{'source':'csv','messages':1,'complaints':1},{'source':'text','messages':3,'complaints':2}]
    with client.app.state.engine.connect() as connection:
        expected=connection.execute(text('SELECT count(*) FROM complaints WHERE is_demo=1 AND is_complaint=1 AND system_name IS NOT NULL')).scalar()
    assert info['known_system_complaints']==expected
    real=client.get('/api/dashboard/overview').json()
    assert real['sources']==[] and real['dated_complaints']==0 and real['no_review_required_messages']==0


def test_equal_length_period_comparison_respects_scope_system_and_riyadh(client):
    # Selected Oct 29–30; prior period Oct 27–28, Riyadh boundaries.
    analyze(client,source_id='previous',source_app='ألف',original_event_time='2026-10-26T21:30:00Z')
    analyze(client,source_id='outside',source_app='ألف',original_event_time='2026-10-26T18:00:00Z')
    analyze(client,source_id='another-system',source_app='باء',original_event_time='2026-10-28T10:00:00Z')
    for id,stamp in [('current-1','2026-10-28T21:30:00Z'),('current-2','2026-10-30T20:30:00Z')]:
        analyze(client,source_id=id,source_app='ألف',original_event_time=stamp)
    analyze(client,'شكرا التطبيق ممتاز',source_id='not-complaint',source_app='ألف',original_event_time='2026-10-29T10:00:00Z')
    analyze(client,source_id='undated',source_app='ألف')
    url='/api/dashboard/overview?data_scope=demo&system=ألف&date_from=2026-10-29&date_to=2026-10-30'
    info=client.get(url).json()
    assert info['total_messages']==3 and info['complaints']==2
    assert info['comparison']=={'date_from':'2026-10-27','date_to':'2026-10-28','previous_complaints':1,
        'current_complaints':2,'complaint_delta':1,'complaint_change_ratio':1.0}
    assert client.get(url.replace('data_scope=demo','data_scope=real')).json()['comparison']['previous_complaints']==0
    assert client.get(url+'&source=csv').json()['comparison']['current_complaints']==0


def test_no_fabricated_change_ratio_or_implicit_comparison(client):
    analyze(client,source_id='only-current',original_event_time='2026-10-29T10:00:00Z')
    result=client.get('/api/dashboard/overview?data_scope=demo&date_from=2026-10-29&date_to=2026-10-29').json()
    assert result['comparison']['complaint_change_ratio'] is None
    assert result['comparison']['previous_complaints']==0 and result['comparison']['complaint_delta']==1
    assert client.get('/api/dashboard/overview?data_scope=demo&date_from=2026-10-29').json()['comparison'] is None
