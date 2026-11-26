"""One marked question, as the API returns it to the detail page."""

from pydantic import BaseModel, ConfigDict


class QuestionMarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_no: str
    title: str
    max_marks: float
    awarded_marks: float
    status: str
    accuracy: float
    scheme_expectation: str
    student_answer: str
    feedback: str
    improvement_tips: list[str]
    knowledge_gap: str
    sort_order: int