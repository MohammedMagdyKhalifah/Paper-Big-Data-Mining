from datetime import datetime, timezone
from typing import Annotated, Literal
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

Category = Literal['AUTH', 'AVAIL', 'PERF', 'TRANS', 'UX', 'OTHER']
CATEGORIES = ['AUTH', 'AVAIL', 'PERF', 'TRANS', 'UX', 'OTHER']
Score = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]

class Prediction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    is_complaint: StrictBool
    complaint_score: Score | None
    category: Category | None
    category_score: Score | None
    needs_review: StrictBool
    model_version: str = Field(min_length=1)

    @field_validator('complaint_score', 'category_score', mode='before')
    @classmethod
    def valid_score(cls, value):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int,float))):
            raise ValueError('الدرجة يجب أن تكون عددًا أو null')
        return value

    @field_validator('model_version')
    @classmethod
    def version_not_blank(cls, value):
        if not value.strip(): raise ValueError('نسخة النموذج فارغة')
        return value

    @model_validator(mode='after')
    def consistent(self):
        if not self.is_complaint and self.category is not None:
            raise ValueError('غير الشكوى يجب ألا تحمل فئة')
        return self

class AnalyzeRequest(BaseModel):
    is_demo: StrictBool = False
    text: str = Field(min_length=1, max_length=20000)
    source_id: str | None = Field(default=None, max_length=200)
    source_app: str | None = Field(default=None, max_length=200)
    original_event_time: datetime | None = None

    @field_validator('text')
    @classmethod
    def text_not_blank(cls, value):
        value = value.strip()
        if not value: raise ValueError('اكتب نصًا غير فارغ')
        return value

    @field_validator('source_id','source_app')
    @classmethod
    def empty_to_none(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator('original_event_time', mode='before')
    @classmethod
    def missing_date(cls, value):
        return None if value == '' else value

    @field_validator('original_event_time')
    @classmethod
    def utc_date(cls, value):
        if value is None: return None
        if value.tzinfo is None: value=value.replace(tzinfo=ZoneInfo('Asia/Riyadh'))
        return value.astimezone(timezone.utc)

class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    is_complaint: StrictBool
    category: Category | None
    system_name: str | None = Field(max_length=200)
    needs_review: StrictBool = False

    @model_validator(mode='after')
    def consistent(self):
        if not self.is_complaint: self.category=None
        self.system_name=(self.system_name or '').strip() or None
        return self

class CorrectionOut(BaseModel):
    id: int
    field_name: str
    old_value: object | None
    new_value: object | None
    corrected_at: datetime

class ComplaintOut(Prediction):
    id: int
    source: str
    source_id: str | None
    source_app: str | None
    original_event_time: datetime | None
    imported_at: datetime
    text_redacted: str
    system_name: str | None
    system_evidence: str
    is_demo: bool
    original_prediction: Prediction
    original_system_name: str | None
    system_reviewed: bool
    corrections: list[CorrectionOut] = Field(default_factory=list)

class AnalyzeResponse(BaseModel):
    message: ComplaintOut
    duplicate: bool

class ListResponse(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int

class RowError(BaseModel):
    row: int
    reason: str

class ImportResponse(BaseModel):
    accepted: int
    duplicates: int
    failed: int
    processed: int
    errors: list[RowError]
    stopped: bool = False
    integration_error: str | None = None

class AnalyticsMeta(BaseModel):
    data_scope: Literal['real','demo']
    time_basis: Literal['event','import']

class CategoryCount(BaseModel):
    category: Category
    count: int

class SourceCount(BaseModel):
    source: str
    messages: int
    complaints: int

class PeriodComparison(BaseModel):
    date_from: str
    date_to: str
    previous_complaints: int
    current_complaints: int
    complaint_delta: int
    complaint_change_ratio: float | None

class OverviewResponse(AnalyticsMeta):
    total_messages: int
    complaints: int
    complaint_ratio: float
    needs_review: int
    categories: list[CategoryCount]
    uncategorized_complaints: int
    no_review_required_messages: int
    known_system_complaints: int
    dated_complaints: int
    sources: list[SourceCount]
    comparison: PeriodComparison | None

class SystemItem(BaseModel):
    name: str | None
    count: int
    share: float
    categories: dict[str,int]

class SystemsResponse(AnalyticsMeta):
    total_complaints: int
    items: list[SystemItem]

class TrendPoint(BaseModel):
    date: str
    count: int

class TrendsResponse(AnalyticsMeta):
    interval: Literal['day','week','month']
    missing_event_time: int
    points: list[TrendPoint]

class ModelInfoResponse(BaseModel):
    mode: Literal['mock','real']
    model_version: str | None
    observed_versions: list[str]
    status: Literal['mock','verified','not_tested','error']
    integration_error: str | None
    categories: list[Category]
    evaluation_available: bool
    evaluation_report: str | None
    evaluation_model_version: str | None
