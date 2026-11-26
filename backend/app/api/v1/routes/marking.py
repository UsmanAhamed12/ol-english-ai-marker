"""Acting on one paper: mark it again, delete it, or download the original scan."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.routes.papers import own_paper
from app.core.limits import limiter
from app.models import MarkingJob, QuestionMark, User
from app.rag import retriever
from app.schemas import PaperSummary
from app.services.marking_service import run_marking
from app.utils import files as storage

router = APIRouter(prefix="/api/papers", tags=["marking"])


@router.post("/{paper_id}/mark", response_model=PaperSummary)
@limiter.limit("30/hour")
def remark_paper(
    request: Request,
    paper_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkingJob:
    """Mark the stored files again, for example after changing the model."""
    job = own_paper(db, paper_id, user)
    if job.status in {"extracting", "marking"}:
        raise HTTPException(status.HTTP_409_CONFLICT, "This paper is already being marked.")

    job.status = "extracting"
    job.error_message = ""
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_marking, job.id)
    return job


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(
    paper_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    """Remove the paper, its question marks, its files and its worked example."""
    job = own_paper(db, paper_id, user)
    storage.remove_all(list(job.script_files or []) + list(job.scheme_files or []))
    retriever.delete_example(job.id)
    db.query(QuestionMark).filter(QuestionMark.job_id == job.id).delete()
    db.delete(job)
    db.commit()


@router.get("/{paper_id}/files/{index}")
def download_script(
    paper_id: str,
    index: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Send back the original scan, so the teacher can check a mark against it."""
    job = own_paper(db, paper_id, user)
    files = list(job.script_files or [])
    if index < 0 or index >= len(files):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found.")

    record = files[index]
    path = storage.resolve(record["relative"])
    media = "application/pdf" if path.suffix.lower() == ".pdf" else "image/jpeg"
    return FileResponse(path, media_type=media, filename=record.get("name") or path.name)