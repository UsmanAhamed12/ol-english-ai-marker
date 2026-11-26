import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarkingJob(Base):
    __tablename__ = "marking_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    student_name: Mapped[str] = mapped_column(String(200), default="")
    paper_title: Mapped[str] = mapped_column(String(200), default="")
    paper_type: Mapped[str] = mapped_column(String(20), default="Full paper")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)

    script_files: Mapped[list] = mapped_column(JSON, default=list)
    scheme_files: Mapped[list] = mapped_column(JSON, default=list)

    extracted_script: Mapped[str] = mapped_column(Text, default="")
    extracted_scheme: Mapped[str] = mapped_column(Text, default="")

    total_awarded: Mapped[float] = mapped_column(Float, default=0)
    total_max: Mapped[float] = mapped_column(Float, default=0)
    normalized_score: Mapped[float] = mapped_column(Float, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0)
    accuracy_note: Mapped[str] = mapped_column(Text, default="")

    overall_feedback: Mapped[str] = mapped_column(Text, default="")
    overall_tips: Mapped[list] = mapped_column(JSON, default=list)
    knowledge_gaps: Mapped[list] = mapped_column(JSON, default=list)
    review_notes: Mapped[list] = mapped_column(JSON, default=list)

    error_message: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    marked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    questions: Mapped[list["QuestionMark"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="QuestionMark.sort_order"
    )


class QuestionMark(Base):
    __tablename__ = "question_marks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("marking_jobs.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)

    question_no: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300), default="")
    max_marks: Mapped[float] = mapped_column(Float, default=0)
    awarded_marks: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="partial")
    accuracy: Mapped[float] = mapped_column(Float, default=0)

    scheme_expectation: Mapped[str] = mapped_column(Text, default="")
    student_answer: Mapped[str] = mapped_column(Text, default="")
    feedback: Mapped[str] = mapped_column(Text, default="")
    improvement_tips: Mapped[list] = mapped_column(JSON, default=list)
    knowledge_gap: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    job: Mapped[MarkingJob] = relationship(back_populates="questions")


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(30), default="Syllabus")
    year: Mapped[str] = mapped_column(String(40), default="")
    notes: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Chunk(Base):
    """One chunk of a knowledge source, scored by keyword overlap (services/rag.py)."""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_sources.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)

    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    terms: Mapped[str] = mapped_column(Text, default="")
    length: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped[KnowledgeSource] = relationship(back_populates="chunks")