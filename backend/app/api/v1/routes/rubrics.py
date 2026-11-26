"""The teacher's knowledge base: syllabus, past papers, schemes and guidance.

These routes stay thin on purpose. Everything that decides what may be stored and
how it is indexed lives in ``app/services/rubric_service.py``, so the same rules
apply when documents are bulk-loaded from the command line.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.limits import limiter
from app.models import KnowledgeSource, User
from app.rag.llm import AIError
from app.schemas import KnowledgeIn, KnowledgeOut
from app.services import ingestion_service, rubric_service

router = APIRouter(prefix="/api/knowledge", tags=["rubrics"])


@router.post("", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/hour")
def create_source(
    request: Request,
    payload: KnowledgeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeSource:
    """Store text that was pasted in, rather than uploaded as a file."""
    return rubric_service.store_source(
        db, user, payload.title, payload.kind, payload.year, payload.notes, payload.content
    )


@router.post("/upload", response_model=KnowledgeOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/hour")
async def upload_source(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(..., max_length=200),
    kind: str = Form("Syllabus"),
    year: str = Form("", max_length=40),
    notes: str = Form("", max_length=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeSource:
    """Read a PDF or photo locally with GLM-OCR, then index the text."""
    try:
        content, flags = await ingestion_service.read_upload([file])
    except AIError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - a bad file is the teacher's problem to fix
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"This document could not be read ({type(exc).__name__}). Try a PDF or a clearer photo.",
        ) from exc

    if len((content or "").strip()) < rubric_service.MIN_CHARS:
        reason = flags[0] if flags else "no text was found on its pages"
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"No readable text in this document ({reason}). Try a clearer scan, or paste the text instead.",
        )

    return rubric_service.store_source(db, user, title, kind, year, notes, content)


@router.get("", response_model=list[KnowledgeOut])
def list_sources(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[KnowledgeSource]:
    """Everything this teacher has stored, plus the four starter sources."""
    return rubric_service.list_sources(db, user)


@router.get("/stats")
def vector_stats(user: User = Depends(get_current_user)) -> dict:
    """How many chunks are indexed, knowledge versus worked examples."""
    return rubric_service.counts(user)


@router.post("/index-papers")
@limiter.limit("10/hour")
def index_marked_papers(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Store every marked paper as a worked example in the knowledge base."""
    return rubric_service.index_marked_papers(db, user)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    rubric_service.delete_source(db, user, source_id)