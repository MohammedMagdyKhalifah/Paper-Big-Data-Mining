"""Local P1 boundary: server-owned OCR drafts and immutable, atomic provenance."""
import hashlib
import io
import json
import os
import sys
from copy import deepcopy
from datetime import timedelta, timezone
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from ..database import Complaint, Correction, OCRDraft, P1Record, now
from ..p1_schemas import OCRResult, P1Analysis
from .classifier_adapter import IntegrationError
from .ingestion import redact

MAX_UPLOAD = 10 * 1024 * 1024
MAX_TEXT = 20000

@lru_cache(maxsize=4)
def verify_ocr_assets(engine, tessdata_dir):
    """Fail before EasyOCR can try downloading a missing/corrupt model."""
    if engine not in {'easyocr','tesseract'}: return
    root=Path(__file__).resolve().parents[3]
    receipts=json.loads((root/'app/P1_OCR_ASSETS.json').read_text())['files']
    for relative,expected in receipts.items():
        if f'/ocr/{"easyocr" if engine=="easyocr" else "tessdata"}/' not in relative: continue
        path=Path(tessdata_dir)/Path(relative).name if engine=='tesseract' and tessdata_dir else root/relative
        if not path.is_file(): raise IntegrationError('ملفات OCR المحلية مفقودة؛ راجع إعداد P1 دون تنزيل تلقائي')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=expected:
                raise IntegrationError('بصمة ملف OCR لا تطابق النسخة المعتمدة؛ أعد نقل الملف المحلي')

class P1Service:
    def extract(self, raw):
        try:
            # Validate the upload header before loading an OCR engine. Pillow's
            # own decompression-bomb exception is not handled by the ML decoder.
            from PIL import Image, UnidentifiedImageError
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    if image.format not in {'PNG','JPEG'} or image.width*image.height>40_000_000:
                        raise HTTPException(422,'الصورة يجب أن تكون PNG أو JPEG وبحد أقصى 40MP')
            except (Image.DecompressionBombError,UnidentifiedImageError,OSError,SyntaxError,ValueError):
                raise HTTPException(422,'تعذر قراءة الصورة؛ استخدم ملف PNG أو JPEG صالحًا بحجم لا يتجاوز 40MP') from None
            engine=os.getenv('ML_OCR_ENGINE','vision' if sys.platform=='darwin' else 'easyocr')
            verify_ocr_assets(engine,os.getenv('ML_TESSDATA_DIR',''))
            result = import_module('ml.analyze').extract_text(raw)
            # Keep the application's established privacy boundary. Coordinates stay
            # image coordinates; system spans will refer to the redacted model text.
            result = deepcopy(result)
            result['text'] = redact(result['text'])
            for line in result['lines']: line['text'] = redact(line['text'])
            if len(result['text']) > MAX_TEXT:
                raise HTTPException(413,'نص الصورة يتجاوز 20000 حرف؛ استخدم لقطة أصغر')
            return OCRResult.model_validate(result).model_dump(exclude_unset=True)
        except (HTTPException,IntegrationError): raise
        except Exception as error:
            raise IntegrationError('تعذر تشغيل OCR المحلي؛ تحقق من المحرك واعتمادياته') from error

    def analyze(self, predictor, **kwargs):
        if predictor.mode != 'real':
            raise IntegrationError('تحليل P1 متاح مع النموذج الحقيقي فقط؛ أوقف وضع Mock')
        try:
            result = P1Analysis.model_validate(import_module('ml.analyze').analyze(**kwargs))
            if result.prediction:
                predictor.last_version = result.prediction.model_version
                predictor.last_error = None
            return result.model_dump()
        except Exception as error:
            predictor.last_error = f'{type(error).__name__}: {error}'
            raise IntegrationError('تعذر تشغيل تحليل P1 الحقيقي؛ تحقق من ملفات النموذج المحلي') from error


def create_draft(session, raw, service):
    if not raw: raise HTTPException(422,'الصورة فارغة')
    if len(raw) > MAX_UPLOAD: raise HTTPException(413,'حجم الصورة يتجاوز 10MB')
    # Expired drafts contain text only, never image files. Bound the local backlog.
    session.execute(delete(OCRDraft).where(OCRDraft.expires_at <= now()))
    session.commit()
    if session.scalar(select(func.count()).select_from(OCRDraft)) >= 100:
        raise HTTPException(429,'توجد صور كثيرة قيد المراجعة؛ حاول لاحقًا')
    result = service.extract(raw)
    if result['status'] == 'failed':
        code=result['error']['code']
        if code == 'engine_error':
            raise HTTPException(503,'فشل محرك OCR المحلي؛ جرّب تشغيلًا عاديًا خارج sandbox أو محرك fallback الموثق')
        raise HTTPException(422,'تعذر قراءة الصورة؛ استخدم ملف PNG أو JPEG صالحًا بحجم لا يتجاوز 40MP')
    draft = OCRDraft(id=str(uuid4()),image_sha256=hashlib.sha256(raw).hexdigest(),
                     result=result,expires_at=now()+timedelta(hours=24))
    session.add(draft); session.commit()
    return {'draft_id':draft.id,'expires_at':draft.expires_at,'ocr':draft.result}


def analyze_and_store(session, request, predictor, service):
    if predictor.mode != 'real': raise IntegrationError('تحليل P1 متاح مع النموذج الحقيقي فقط؛ أوقف وضع Mock')
    draft = None
    if request.draft_id:
        draft=session.get(OCRDraft,str(request.draft_id))
        if draft is None: raise HTTPException(404,'نص الصورة غير موجود؛ أعد رفع الصورة')
        expiry=draft.expires_at.replace(tzinfo=timezone.utc) if draft.expires_at.tzinfo is None else draft.expires_at
        if expiry <= now(): raise HTTPException(410,'انتهت صلاحية نص الصورة؛ أعد استخراج النص')
    typed=redact(request.text.strip())
    corrected=redact(request.corrected_text.strip()) if request.corrected_text is not None else None
    classified='\n'.join(x for x in [typed,corrected if corrected is not None else draft.result['text'] if draft else ''] if x)
    if len(classified)>MAX_TEXT: raise HTTPException(422,'إجمالي النص المرسل للنموذج يتجاوز 20000 حرف')
    source='image' if draft else 'text'
    source_app=redact(request.source_app) if request.source_app else None
    source_id=redact(request.source_id) if request.source_id else None
    demo=request.is_demo or bool(source_id and source_id.upper().startswith('DEMO-'))
    # Include OCR provenance and model identity: repeated uploads deduplicate without
    # erasing a different OCR correction, image, context or model-version result.
    if predictor.last_version is None: predictor.predict('تجربة تحميل النموذج')
    context=['p1-analysis-v1',predictor.last_version,source,demo,source_id,source_app,
             request.original_event_time.isoformat() if request.original_event_time else None,
             typed,corrected,draft.image_sha256 if draft else None,draft.result if draft else None]
    if draft: context[-1]={k:v for k,v in draft.result.items() if k!='elapsed_ms'}
    fingerprint=hashlib.sha256(json.dumps(context,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    existing=session.scalar(select(Complaint).where(Complaint.fingerprint==fingerprint))
    if existing is not None:
        return existing,True,existing.p1_record.result
    result=service.analyze(predictor,text=typed or None,image_ocr=deepcopy(draft.result) if draft else None,corrected_text=corrected)
    if result['prediction'] is None: return None,False,result
    matches=result['systems']['systems']
    # One definite mention can populate the existing aggregate field. Multiple or
    # uncertain mentions remain in immutable evidence, never guess a primary system.
    name=matches[0]['name_ar'] if len(matches)==1 else None
    message=Complaint(source=source,source_id=source_id,source_app=source_app,
        original_event_time=request.original_event_time,text_redacted=result['input']['classified_text'],
        **result['prediction'],system_name=name,original_system_name=name,
        system_evidence='explicit_mention' if name else 'multiple_mentions' if matches else 'unknown',
        is_demo=demo,fingerprint=fingerprint,original_prediction=result['prediction'])
    message.p1_record=P1Record(result=result,image_sha256=draft.image_sha256 if draft else None)
    session.add(message)
    try:
        session.flush()
        if draft and corrected is not None and corrected != draft.result['text']:
            session.add(Correction(message_id=message.id,field_name='ocr_text',
                old_value=draft.result['text'],new_value=corrected))
        session.commit()
    except IntegrityError:
        session.rollback()
        existing=session.scalar(select(Complaint).where(Complaint.fingerprint==fingerprint))
        if existing is None: raise
        return existing,True,existing.p1_record.result
    return message,False,result
