"""Models for the knowledge base: a syllabus, past paper, scheme or guidance note."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    kind: str = Field(default="Syllabus", pattern="^(Syllabus|Past paper|Marking scheme|Guidance)$")
    year: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=500)
    content: str = Field(default="", max_length=120000)


class KnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    kind: str
    year: str
    notes: str
    chunk_count: int
    created_at: datetime