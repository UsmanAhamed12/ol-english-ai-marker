"""A marked paper: the summary used in lists, and the full record used in detail."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.marking import QuestionMarkOut


class PaperSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_name: str
    paper_title: str
    paper_type: str
    status: str
    normalized_score: float
    accuracy: float
    created_at: datetime
    marked_at: datetime | None


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_name: str
    paper_title: str
    paper_type: str
    status: str
    total_awarded: float
    total_max: float
    normalized_score: float
    accuracy: float
    accuracy_note: str
    overall_feedback: str
    overall_tips: list[str]
    knowledge_gaps: list[str]
    review_notes: list[str]
    error_message: str
    created_at: datetime
    marked_at: datetime | None
    questions: list[QuestionMarkOut] = []