from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import HTTPException, Query
from sqlalchemy import case, func, select
from ..database import Complaint
from ..schemas import CATEGORIES

RIYADH=ZoneInfo('Asia/Riyadh')

class Filters:
    def __init__(self, data_scope: str=Query('real',pattern='^(real|demo)$'),
                 source: str | None=Query(None,pattern='^(text|csv|image)$'), system: str | None=None,
                 date_from: date | None=None, date_to: date | None=None,
                 time_basis: str=Query('event',pattern='^(event|import)$')):
        if date_from and date_to and date_from>date_to:
            raise HTTPException(422,'بداية الفترة يجب أن تسبق نهايتها')
        self.data_scope=data_scope;self.source=source;self.system=system
        self.date_from=date_from;self.date_to=date_to;self.time_basis=time_basis

    def conditions(self, dates=True):
        clauses=[Complaint.is_demo == (self.data_scope=='demo')]
        if self.source: clauses.append(Complaint.source==self.source)
        if self.system=='__unknown__': clauses.append(Complaint.system_name.is_(None))
        elif self.system: clauses.append(Complaint.system_name==self.system)
        column=Complaint.original_event_time if self.time_basis=='event' else Complaint.imported_at
        if dates:
            if self.date_from:
                clauses.append(column>=datetime.combine(self.date_from,time.min,RIYADH).astimezone(timezone.utc))
            if self.date_to:
                clauses.append(column<datetime.combine(self.date_to+timedelta(days=1),time.min,RIYADH).astimezone(timezone.utc))
        return clauses

    def metadata(self): return {'data_scope':self.data_scope,'time_basis':self.time_basis}


def overview(session, filters):
    clauses=filters.conditions()
    def count(*extra): return session.scalar(select(func.count()).select_from(Complaint).where(*clauses,*extra)) or 0
    total=count(); complaints=count(Complaint.is_complaint.is_(True))
    counts=dict(session.execute(select(Complaint.category,func.count()).where(*clauses,Complaint.is_complaint.is_(True)).group_by(Complaint.category)).all())
    sources=session.execute(select(Complaint.source,func.count(),func.sum(case((Complaint.is_complaint.is_(True),1),else_=0)))
        .where(*clauses).group_by(Complaint.source).order_by(Complaint.source)).all()
    comparison=None
    if filters.date_from and filters.date_to:
        days=(filters.date_to-filters.date_from).days+1
        try:
            previous_from=filters.date_from-timedelta(days=days)
            previous_to=filters.date_from-timedelta(days=1)
            start=datetime.combine(previous_from,time.min,RIYADH).astimezone(timezone.utc)
            end=datetime.combine(filters.date_from,time.min,RIYADH).astimezone(timezone.utc)
        except (OverflowError,ValueError):
            raise HTTPException(422,'الفترة المحددة خارج مجال المقارنة')
        column=Complaint.original_event_time if filters.time_basis=='event' else Complaint.imported_at
        previous=session.scalar(select(func.count()).select_from(Complaint).where(*filters.conditions(dates=False),
            Complaint.is_complaint.is_(True),column>=start,column<end)) or 0
        comparison={'date_from':previous_from.isoformat(),'date_to':previous_to.isoformat(),
            'previous_complaints':previous,'current_complaints':complaints,'complaint_delta':complaints-previous,
            'complaint_change_ratio':(complaints-previous)/previous if previous else None}
    return {**filters.metadata(),'total_messages':total,'complaints':complaints,
        'no_review_required_messages':count(Complaint.needs_review.is_(False)),
        'known_system_complaints':count(Complaint.is_complaint.is_(True),Complaint.system_name.is_not(None)),
        'dated_complaints':count(Complaint.is_complaint.is_(True),Complaint.original_event_time.is_not(None)),
        'sources':[{'source':s,'messages':n,'complaints':int(c or 0)} for s,n,c in sources],
        'comparison':comparison,
        'complaint_ratio':complaints/total if total else 0,'needs_review':count(Complaint.needs_review.is_(True)),
        'categories':[{'category':c,'count':counts.get(c,0)} for c in CATEGORIES],
        'uncategorized_complaints':counts.get(None,0)}


def systems(session,filters):
    rows=session.execute(select(Complaint.system_name,Complaint.category,func.count())
        .where(*filters.conditions(),Complaint.is_complaint.is_(True))
        .group_by(Complaint.system_name,Complaint.category)).all()
    grouped={}; total=sum(n for _,_,n in rows)
    for name,category,n in rows:
        item=grouped.setdefault(name,{'name':name,'count':0,'categories':{}})
        item['count']+=n;item['categories'][category or 'UNCLASSIFIED']=n
    items=sorted(grouped.values(),key=lambda x:(-x['count'],x['name'] or ''))
    for item in items: item['share']=item['count']/total if total else 0
    return {**filters.metadata(),'total_complaints':total,'items':items}


def trends(session,filters,interval):
    column=Complaint.original_event_time if filters.time_basis=='event' else Complaint.imported_at
    rows=session.execute(select(column).where(*filters.conditions(),Complaint.is_complaint.is_(True),column.is_not(None))).scalars()
    counts=Counter()
    for stamp in rows:
        if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=timezone.utc)
        day=stamp.astimezone(RIYADH).date()
        if interval=='week': day-=timedelta(days=day.weekday())
        if interval=='month': day=day.replace(day=1)
        counts[day.isoformat()]+=1
    missing=session.scalar(select(func.count()).select_from(Complaint).where(*filters.conditions(dates=False),
        Complaint.is_complaint.is_(True),Complaint.original_event_time.is_(None))) or 0
    return {**filters.metadata(),'interval':interval,'missing_event_time':missing,
        'points':[{'date':d,'count':n} for d,n in sorted(counts.items())]}
