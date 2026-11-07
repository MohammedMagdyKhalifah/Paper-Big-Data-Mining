"""Additive P1 HTTP contracts. The original six-field Prediction is unchanged."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .schemas import AnalyzeRequest, ComplaintOut, Prediction, Score

class Span(BaseModel):
    text: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)

class Mention(Span):
    basis: str

class PossibleMention(Span):
    system_id: str
    reason: str

class SystemMatch(BaseModel):
    system_id: str
    name_ar: str
    name_en: str
    mentions: list[Mention]

class SystemsEvidence(BaseModel):
    status: Literal['identified','ambiguous','unknown']
    systems: list[SystemMatch]
    possible_mentions: list[PossibleMention]
    generic_references: list[Span]
    registry_version: str
    method: str

class OCRLine(BaseModel):
    text: str
    confidence: Score | None
    bbox: list[float] = Field(min_length=4,max_length=4)

class OCRError(BaseModel):
    code: str
    message: str

class ImageInfo(BaseModel):
    format: Literal['PNG','JPEG']
    width: int
    height: int

class OCRResult(BaseModel):
    status: Literal['ok','empty','failed']
    text: str
    lines: list[OCRLine]
    mean_confidence: Score | None
    low_confidence: bool
    error: OCRError | None
    engine: str
    image: ImageInfo | None
    elapsed_ms: float
    corrected_text: str | None = None
    used_for_classification: str | None = None

class AnalysisInput(BaseModel):
    has_user_text: bool
    has_image: bool
    text_source: str | None
    classified_text: str | None

class ErrorCue(Span):
    cue: str

class Signals(BaseModel):
    error_message_cues: list[ErrorCue]
    narrative_markers: list[str]
    needs_user_context: bool
    ocr_needs_review: bool

class P1Analysis(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['p1-analysis-v1']
    analysis_kind: Literal['complaint','not_complaint','error_screen_signal','no_text','ocr_failed']
    input: AnalysisInput
    prediction: Prediction | None
    systems: SystemsEvidence | None
    signals: Signals
    ocr: OCRResult | None
    notes: list[str]
    timing_ms: dict[str,float]

class OCRDraftOut(BaseModel):
    draft_id: UUID
    expires_at: datetime
    ocr: OCRResult

class P1Request(AnalyzeRequest):
    model_config = ConfigDict(extra='forbid')
    text: str = Field(default='',max_length=20000)
    draft_id: UUID | None = None
    corrected_text: str | None = Field(default=None,max_length=20000)

    @field_validator('text')
    @classmethod
    def text_not_blank(cls, value):
        return value.strip()

    @model_validator(mode='after')
    def usable_input(self):
        if not self.text.strip() and self.draft_id is None:
            raise ValueError('أدخل نصًا أو ارفع صورة واستخرج نصها أولًا')
        if self.corrected_text is not None:
            if self.draft_id is None: raise ValueError('تصحيح OCR يحتاج صورة مستخرجة')
            if not self.corrected_text.strip(): raise ValueError('نص OCR المصحح فارغ')
        return self

class P1Response(BaseModel):
    message: ComplaintOut | None
    duplicate: bool
    analysis: P1Analysis
