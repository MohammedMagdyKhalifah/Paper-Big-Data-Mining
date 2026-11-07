from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

def now(): return datetime.now(timezone.utc)

class Base(DeclarativeBase): pass

class Complaint(Base):
    __tablename__='complaints'
    __table_args__=(CheckConstraint("is_complaint OR category IS NULL", name='noncomplaint_no_category'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[str | None] = mapped_column(String(200))
    source_app: Mapped[str | None] = mapped_column(String(200))
    original_event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    text_redacted: Mapped[str] = mapped_column(Text)
    is_complaint: Mapped[bool] = mapped_column(Boolean, index=True)
    complaint_score: Mapped[float | None] = mapped_column(Float)
    category: Mapped[str | None] = mapped_column(String(10), index=True)
    category_score: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(200))
    system_name: Mapped[str | None] = mapped_column(String(200), index=True)
    system_evidence: Mapped[str] = mapped_column(String(30))
    needs_review: Mapped[bool] = mapped_column(Boolean, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    original_prediction: Mapped[dict] = mapped_column(JSON)
    original_system_name: Mapped[str | None] = mapped_column(String(200))
    system_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

class Correction(Base):
    __tablename__='corrections'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey('complaints.id'), index=True)
    field_name: Mapped[str] = mapped_column(String(50))
    old_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    corrected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

def setup_database(url):
    if url.startswith('sqlite:///'):
        path=url.removeprefix('sqlite:///')
        if path != ':memory:': Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine=create_engine(url, connect_args={'check_same_thread':False} if url.startswith('sqlite') else {})
    if engine.dialect.name=='sqlite':
        @event.listens_for(engine, 'connect')
        def configure(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=5000')
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)
