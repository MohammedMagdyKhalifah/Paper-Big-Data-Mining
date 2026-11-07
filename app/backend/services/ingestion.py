import hashlib
import json
import re
from datetime import timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..database import Complaint, Correction


def redact(text):
    text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[بريد محجوب]', text)
    text=re.sub(r'(?<!\w)(?:\+?966[\s-]?|0)5(?:[\s-]?\d){8}(?!\d)', '[هاتف محجوب]', text)
    return re.sub(r'(?<!\d)[12]\d{9}(?!\d)', '[هوية محجوبة]', text)


def ingest(session, request, predictor, source='text'):
    text=redact(request.text)
    source_app=redact(request.source_app) if request.source_app else None
    is_demo=predictor.mode=='mock' or request.is_demo or bool(request.source_id and request.source_id.upper().startswith('DEMO-'))
    context=[is_demo,source,source_app]
    if request.source_id:
        context+=['id',request.source_id]
    else:
        context+=['content',text,request.original_event_time.isoformat() if request.original_event_time else None]
    fingerprint=hashlib.sha256(json.dumps(context,ensure_ascii=False).encode()).hexdigest()
    existing=session.scalar(select(Complaint).where(Complaint.fingerprint==fingerprint))
    if existing: return existing, True
    result=predictor.predict(text)
    message=Complaint(source=source,source_id=redact(request.source_id) if request.source_id else None,
        source_app=source_app,original_event_time=request.original_event_time,text_redacted=text,
        **result.model_dump(), system_name=source_app,original_system_name=source_app,
        system_evidence='source_metadata' if source_app else 'unknown',is_demo=is_demo,
        fingerprint=fingerprint,original_prediction=result.model_dump())
    session.add(message)
    try: session.commit()
    except IntegrityError:
        session.rollback()
        existing=session.scalar(select(Complaint).where(Complaint.fingerprint==fingerprint))
        if existing is None: raise
        return existing,True
    return message,False


def iso(value):
    if value is None: return None
    if value.tzinfo is None: value=value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def serialize(message, corrections=None):
    data={column.name:getattr(message,column.name) for column in Complaint.__table__.columns if column.name!='fingerprint'}
    for field in ['imported_at','original_event_time']: data[field]=iso(data[field])
    if corrections is not None:
        data['corrections']=[{'id':c.id,'field_name':c.field_name,'old_value':c.old_value,
            'new_value':c.new_value,'corrected_at':iso(c.corrected_at)} for c in corrections]
    return data


def review(session,message,request):
    for field,value in request.model_dump().items():
        if field=='system_name' and value: value=redact(value)
        previous=getattr(message,field)
        if previous != value:
            session.add(Correction(message_id=message.id,field_name=field,old_value=previous,new_value=value))
            setattr(message,field,value)
            if field=='system_name': message.system_reviewed=True
    session.commit()
    return message
