import csv
import io
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from .database import Complaint, Correction, setup_database
from .schemas import ModelInfoResponse, OverviewResponse, SystemsResponse, TrendsResponse, AnalyzeRequest, AnalyzeResponse, CATEGORIES, Category, ComplaintOut, ImportResponse, ListResponse, ReviewRequest
from .services.analytics import Filters, overview, systems, trends
from .services.classifier_adapter import IntegrationError, get_predictor
from .services.ingestion import ingest, review, serialize
from .p1_schemas import OCRDraftOut, P1Request, P1Response
from .services.p1 import MAX_UPLOAD, P1Service, analyze_and_store, create_draft

DEFAULT_DB=Path(__file__).parent/'storage'/'complaints.sqlite3'
BUNDLE=Path(__file__).resolve().parents[1]
BUNDLED_MODEL_VERSION=json.loads((BUNDLE/'MODEL_ASSETS.json').read_text())['model_version']
BUNDLED_EVALUATION=BUNDLE.parent/'ml'/'reports'/'evaluation.md'
A4_ARTIFACT_DIR=BUNDLE.parent/'ml'/'artifacts'/'a4'/'export'/'a4-marbert-v1'
A4_EVALUATION=BUNDLE.parent/'ml'/'reports'/'a4_model_card.md'


def create_app(database_url=None, predictor=None, p1_service=None):
    engine, sessions=setup_database(database_url or os.getenv('DATABASE_URL',f'sqlite:///{DEFAULT_DB}'))
    predictor=predictor or get_predictor(os.getenv('APP_ML_MODE','real'))
    p1_service=p1_service or P1Service()
    @asynccontextmanager
    async def lifespan(_):
        # Keep diagnostics available if local artifacts are missing. Analyze then
        # returns 503, never a silent Mock fallback.
        if hasattr(predictor,'warmup'):
            try:
                predictor.warmup()
            except IntegrationError:
                pass  # Adapter records the load error for /models/info.
        try:
            yield
        finally:
            engine.dispose()
    api=FastAPI(title='مرصد الشكاوى الرقمية',version='0.1.0',lifespan=lifespan)
    api.state.engine=engine;api.state.sessions=sessions;api.state.predictor=predictor
    router=APIRouter(prefix='/api')
    def session_dep():
        with sessions() as session: yield session

    @api.exception_handler(RequestValidationError)
    async def validation_error(_, error):
        # Do not echo rejected user text or arbitrary input in error responses.
        return JSONResponse(status_code=422,content={'detail':[{'loc':list(e['loc']),'msg':e['msg']} for e in error.errors()]})

    @api.exception_handler(IntegrationError)
    async def integration_error(_,error):
        return JSONResponse(status_code=503,content={'detail':str(error)})

    @router.post('/complaints/analyze',response_model=AnalyzeResponse)
    def analyze(body:AnalyzeRequest,session=Depends(session_dep)):
        message,duplicate=ingest(session,body,predictor)
        return {'message':serialize(message),'duplicate':duplicate}

    @router.post('/ocr/extract',response_model=OCRDraftOut)
    def extract_image(file:UploadFile=File(...),session=Depends(session_dep)):
        if predictor.mode!='real': raise IntegrationError('OCR متاح في مسار P1 الحقيقي فقط؛ أوقف وضع Mock')
        if Path(file.filename or '').suffix.lower() not in {'.png','.jpg','.jpeg'}:
            raise HTTPException(422,'اختر صورة PNG أو JPG أو JPEG')
        raw=file.file.read(MAX_UPLOAD+1)
        return create_draft(session,raw,p1_service)

    @router.post('/complaints/analyze-p1',response_model=P1Response)
    def analyze_p1(body:P1Request,session=Depends(session_dep)):
        message,duplicate,result=analyze_and_store(session,body,predictor,p1_service)
        return {'message':serialize(message) if message else None,'duplicate':duplicate,'analysis':result}

    @router.post('/complaints/import',response_model=ImportResponse)
    def import_csv(file:UploadFile=File(...),is_demo:bool=Form(False),session=Depends(session_dep)):
        raw=file.file.read(10*1024*1024+1)
        if len(raw)>10*1024*1024: raise HTTPException(413,'الملف أكبر من 10MB')
        try:
            content=raw.decode('utf-8-sig')
            reader=csv.DictReader(io.StringIO(content),strict=True)
            fields=reader.fieldnames
            if not fields or 'text' not in fields: raise HTTPException(422,'عمود text مطلوب')
            if len(fields)!=len(set(fields)): raise HTTPException(422,'أسماء أعمدة CSV مكررة')
            rows=list(reader)
            if len(rows)>5000: raise HTTPException(413,'الحد الأقصى 5000 صف')
        except (UnicodeError,csv.Error): raise HTTPException(422,'تعذر قراءة CSV بترميز UTF-8')
        result={'accepted':0,'duplicates':0,'failed':0,'processed':0,'errors':[], 'stopped':False,'integration_error':None}
        for number,row in enumerate(rows,start=2):
            try:
                if None in row: raise ValueError('عدد الخانات لا يطابق الأعمدة')
                request=AnalyzeRequest.model_validate({**{key:row[key] for key in ['text','source_id','source_app','original_event_time'] if key in row},'is_demo':is_demo})
                _,duplicate=ingest(session,request,predictor,'csv')
                result['duplicates' if duplicate else 'accepted']+=1
            except (ValidationError,ValueError) as error:
                reason='؛ '.join(f"{'.'.join(map(str,e['loc']))}: {e['msg']}" for e in error.errors()) if isinstance(error,ValidationError) else str(error)
                result['failed']+=1; result['errors'].append({'row':number,'reason':reason})
            except IntegrationError as error:
                result['stopped']=True;result['integration_error']=str(error)
                result['failed']+=1;result['errors'].append({'row':number,'reason':str(error)})
                result['processed']+=1
                break
            result['processed']+=1
        return result

    @router.get('/complaints',response_model=ListResponse)
    def complaints(filters:Filters=Depends(),q:str=Query('',max_length=200),category:Category | None=None,
                   is_complaint:bool | None=None,needs_review:bool | None=None,
                   page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),session=Depends(session_dep)):
        clauses=filters.conditions()
        if q: clauses.append(Complaint.text_redacted.contains(q,autoescape=True))
        if category: clauses.append(Complaint.category==category)
        if is_complaint is not None: clauses.append(Complaint.is_complaint==is_complaint)
        if needs_review is not None: clauses.append(Complaint.needs_review==needs_review)
        total=session.scalar(select(func.count()).select_from(Complaint).where(*clauses))
        rows=session.scalars(select(Complaint).where(*clauses).order_by(Complaint.id.desc()).offset((page-1)*page_size).limit(page_size))
        return {'items':[serialize(m) for m in rows],'total':total,'page':page,'page_size':page_size}

    def find(session,id):
        message=session.get(Complaint,id)
        if message is None: raise HTTPException(404,'الرسالة غير موجودة')
        return message

    def details(session,message):
        edits=session.scalars(select(Correction).where(Correction.message_id==message.id).order_by(Correction.id))
        return serialize(message,list(edits))

    @router.get('/complaints/{id}',response_model=ComplaintOut)
    def detail(id:int,session=Depends(session_dep)): return details(session,find(session,id))

    @router.patch('/complaints/{id}/review',response_model=ComplaintOut)
    def correct(id:int,body:ReviewRequest,session=Depends(session_dep)):
        return details(session,review(session,find(session,id),body))

    @router.get('/dashboard/overview',response_model=OverviewResponse)
    def overview_route(filters:Filters=Depends(),session=Depends(session_dep)): return overview(session,filters)

    @router.get('/dashboard/trends',response_model=TrendsResponse)
    def trends_route(filters:Filters=Depends(),interval:Literal['day','week','month']='day',session=Depends(session_dep)):
        return trends(session,filters,interval)

    @router.get('/systems',response_model=SystemsResponse)
    def systems_route(filters:Filters=Depends(),session=Depends(session_dep)): return systems(session,filters)

    @router.get('/models/info',response_model=ModelInfoResponse)
    def info(session=Depends(session_dep)):
        versions=list(session.scalars(select(Complaint.model_version).where(Complaint.is_demo==(predictor.mode=='mock')).distinct()))
        report=None
        path=os.getenv('APP_EVALUATION_REPORT')
        version=os.getenv('APP_EVALUATION_MODEL_VERSION')
        # Pair only known bundle paths and successfully loaded versions. The A4
        # source report separates holdout subsets, external proxy and non-blind
        # V1 test; never relabel or pool their metrics in the application.
        if path is None and version is None:
            artifact_dir=Path(os.getenv('ML_ARTIFACT_DIR',str(BUNDLE.parent/'ml'/'artifacts'))).resolve()
            if artifact_dir==A4_ARTIFACT_DIR.resolve():
                path=str(A4_EVALUATION);version='a4-marbert-v1'
            elif artifact_dir==(BUNDLE.parent/'ml'/'artifacts').resolve():
                path=str(BUNDLED_EVALUATION);version=BUNDLED_MODEL_VERSION
        if predictor.mode=='real' and path and version and version==predictor.last_version:
            try:
                with Path(path).open(encoding='utf-8') as source: report=source.read(100000)
            except (OSError,UnicodeError): pass
        return {'mode':predictor.mode,'model_version':predictor.last_version,'observed_versions':versions,
            'status':'mock' if predictor.mode=='mock' else ('error' if predictor.last_error else 'verified' if predictor.last_version else 'not_tested'),
            'integration_error':predictor.last_error,'categories':CATEGORIES,'evaluation_available':report is not None,
            'evaluation_report':report,'evaluation_model_version':version if report else None}

    api.include_router(router)
    return api

app=create_app()
