"""All request/response models, re-exported so routes can import from one place.

    from app.schemas import PaperOut, KnowledgeIn

Each group lives in its own module: auth, paper, marking, rubric.
"""

from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.schemas.marking import QuestionMarkOut
from app.schemas.paper import PaperOut, PaperSummary
from app.schemas.rubric import KnowledgeIn, KnowledgeOut

__all__ = [
    "LoginIn",
    "RegisterIn",
    "TokenOut",
    "UserOut",
    "QuestionMarkOut",
    "PaperOut",
    "PaperSummary",
    "KnowledgeIn",
    "KnowledgeOut",
]